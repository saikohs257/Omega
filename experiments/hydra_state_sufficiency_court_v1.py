"""HYDRA latent-state sufficiency court.

Question: are Hazard + Burden + Recovery-minus-Burden a sufficient real-time state,
or does the future still depend on path/timer information once that state is fixed?

Protocol is pre-specified before inspecting 2024 holdout metrics:
- Canonical spine stays immutable.
- State coordinates are H=hazard_score(t-1), B=LiveDeficit(t-1),
  RR=RecoveryWeakness_v1(t-1)-LiveDeficit(t-1).
- History augmentation is limited to prior-state lags, 24h velocities, and
  duration spent in the same discretized H/B/RR state cell.
- Models are fixed logistic regressions; no holdout feature selection.
- Evaluation is walk-forward by year and, for 2024, repeated over all 72 phase
  offsets using real source rows only (never GroupBy.first()).

Strong evidence for a sufficient state is a small, unstable, or null incremental
AUC from the history/timer blocks across phase offsets. Persistent positive
increment after state conditioning falsifies sufficiency and points to hidden
memory, hysteresis, or an omitted timer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hydra_relative_recovery_court_v1 import history

TARGET = "Crash72"
HOLDOUT = 2024
PERIOD = 72
STATE = ["state_hazard", "state_burden", "state_rr"]
LAGS = ["hazard_lag24", "burden_lag24", "rr_lag24"]
VELOCITIES = ["hazard_delta24", "burden_delta24", "rr_delta24"]
TIMER = ["state_cell_dwell_h"]
MODELS = {
    "state": STATE,
    "state_plus_lags": STATE + LAGS,
    "state_plus_timer": STATE + TIMER,
    "state_plus_velocity": STATE + VELOCITIES,
    "state_plus_history": STATE + LAGS + VELOCITIES + TIMER,
}


def clean_target(d: pd.DataFrame) -> pd.Series:
    y = pd.to_numeric(d[TARGET], errors="coerce")
    bad = set(y.dropna().astype(int).unique()) - {0, 1}
    if bad:
        raise ValueError(f"non-binary {TARGET} classes: {sorted(bad)}")
    return y.fillna(0).astype(int)


def add_state_coordinates(raw: pd.DataFrame) -> pd.DataFrame:
    d = history(raw)
    d = d.sort_values("open_time").reset_index(drop=True)
    # All are strictly pre-row quantities.
    d["state_hazard"] = pd.to_numeric(d["hazard_score"], errors="coerce").shift(1)
    d["state_burden"] = pd.to_numeric(d["LiveDeficit"], errors="coerce").shift(1)
    d["state_rr"] = (
        pd.to_numeric(d["RecoveryWeakness_v1"], errors="coerce")
        .shift(1)
        - pd.to_numeric(d["LiveDeficit"], errors="coerce").shift(1)
    )
    d["hazard_lag24"] = d["state_hazard"].shift(24)
    d["burden_lag24"] = d["state_burden"].shift(24)
    d["rr_lag24"] = d["state_rr"].shift(24)
    d["hazard_delta24"] = d["state_hazard"] - d["hazard_lag24"]
    d["burden_delta24"] = d["state_burden"] - d["burden_lag24"]
    d["rr_delta24"] = d["state_rr"] - d["rr_lag24"]
    return d


def quantile_edges(train: pd.DataFrame, col: str, bins: int = 4) -> np.ndarray:
    x = pd.to_numeric(train[col], errors="coerce").dropna().to_numpy(float)
    if len(x) < bins * 10:
        return np.array([])
    q = np.quantile(x, np.linspace(0, 1, bins + 1))
    q = np.unique(q)
    return q if len(q) >= 3 else np.array([])


def apply_cell_edges(d: pd.DataFrame, edges: dict[str, np.ndarray], bins: int = 4) -> pd.Series:
    keys = []
    for col in STATE:
        e = edges[col]
        x = pd.to_numeric(d[col], errors="coerce").to_numpy(float)
        if len(e) < 3:
            b = np.full(len(d), -1, dtype=int)
        else:
            b = np.digitize(x, e[1:-1], right=False)
            b[~np.isfinite(x)] = -1
        keys.append(b.astype(str))
    return pd.Series(keys[0], index=d.index).str.cat(
        [pd.Series(k, index=d.index) for k in keys[1:]], sep="|"
    )


def add_timer(d: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    edges = {c: quantile_edges(train, c, bins=4) for c in STATE}
    cell = apply_cell_edges(d, edges)
    dwell = np.zeros(len(d), dtype=float)
    vals = cell.to_numpy()
    for i, v in enumerate(vals):
        if i and v != "-1|-1|-1" and v == vals[i - 1]:
            dwell[i] = dwell[i - 1] + 1.0
        elif v != "-1|-1|-1":
            dwell[i] = 1.0
        else:
            dwell[i] = 0.0
    d["state_cell"] = cell
    d["state_cell_dwell_h"] = dwell
    return d


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5, solver="liblinear"),
    )
    model.fit(train[cols].astype(float), train[TARGET].astype(int))
    return model.predict_proba(test[cols].astype(float))[:, 1]


def metric(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, int)
    p = np.clip(np.asarray(p, float), 1e-7, 1 - 1e-7)
    two = np.unique(y).size == 2
    return {
        "n": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()),
        "auc": float(roc_auc_score(y, p)) if two else None,
        "pr_auc": float(average_precision_score(y, p)) if two else None,
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "mean_prediction": float(p.mean()),
    }


def nonoverlap(d: pd.DataFrame, offset: int) -> pd.DataFrame:
    x = d.sort_values("open_time").reset_index(drop=True).copy()
    h = pd.to_datetime(x.open_time, utc=True).astype("int64") // 10**9 // 3600
    x["_anchor"] = ((h - offset) // PERIOD) * PERIOD + offset
    return x.drop_duplicates("_anchor", keep="first").reset_index(drop=True)


def evaluate_years(d: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    years = sorted(pd.to_datetime(d.open_time, utc=True).dt.year.unique())
    for year in years:
        if int(year) < 2021:
            continue
        train = d[pd.to_datetime(d.open_time, utc=True).dt.year < year].copy()
        test = d[pd.to_datetime(d.open_time, utc=True).dt.year == year].copy()
        if train.empty or test.empty or train[TARGET].nunique() < 2:
            continue
        train = add_timer(train, train)
        test = add_timer(test, train)
        yt = test[TARGET].to_numpy(int)
        for name, cols in MODELS.items():
            p = fit_predict(train, test, cols)
            rows.append({"year": int(year), "model": name, **metric(yt, p)})
    return rows


def evaluate_holdout_offsets(d: pd.DataFrame) -> list[dict]:
    train = d[pd.to_datetime(d.open_time, utc=True).dt.year < HOLDOUT].copy()
    test_all = d[pd.to_datetime(d.open_time, utc=True).dt.year == HOLDOUT].copy()
    train = add_timer(train, train)
    fitted: dict[str, np.ndarray] = {}
    for name, cols in MODELS.items():
        fitted[name] = fit_predict(train, test_all, cols)
    test_all = test_all.reset_index(drop=True)
    out: list[dict] = []
    # Repeated phase-offset sampling tests whether any gain is an artifact of row overlap.
    for off in range(PERIOD):
        x = nonoverlap(test_all, off)
        idx = x.index.to_numpy()
        y = x[TARGET].to_numpy(int)
        for name, p_all in fitted.items():
            # nonoverlap() preserves original row order after reset; rebuild positions by open_time.
            p_map = dict(zip(test_all.open_time.astype(str), p_all))
            p = np.array([p_map[str(v)] for v in x.open_time], dtype=float)
            out.append({"offset": off, "model": name, **metric(y, p)})
    return out


def summarize_offsets(rows: list[dict]) -> list[dict]:
    frame = pd.DataFrame(rows)
    state = frame[frame.model == "state"].set_index("offset")
    result = []
    for name in MODELS:
        q = frame[frame.model == name]["auc"].dropna()
        delta = None
        if name != "state":
            other = frame[frame.model == name].set_index("offset")["auc"] - state["auc"]
            delta = {
                "median": float(other.median()),
                "q25": float(other.quantile(.25)),
                "q75": float(other.quantile(.75)),
                "min": float(other.min()),
                "max": float(other.max()),
                "positive_offset_fraction": float((other > 0).mean()),
            }
        result.append({
            "model": name,
            "valid_offsets": int(len(q)),
            "median_auc": float(q.median()) if len(q) else None,
            "q25_auc": float(q.quantile(.25)) if len(q) else None,
            "q75_auc": float(q.quantile(.75)) if len(q) else None,
            "min_auc": float(q.min()) if len(q) else None,
            "max_auc": float(q.max()) if len(q) else None,
            "delta_vs_state": delta,
        })
    return result


def matched_history_test(d: pd.DataFrame) -> dict:
    """Case/control match on H/B/RR, then inspect whether timer/history differs."""
    train = d[pd.to_datetime(d.open_time, utc=True).dt.year < HOLDOUT].copy()
    test = d[pd.to_datetime(d.open_time, utc=True).dt.year == HOLDOUT].copy().reset_index(drop=True)
    test = add_timer(test, train)
    y = test[TARGET].to_numpy(int)
    event_idx = np.flatnonzero(y == 1)
    ctrl_idx = np.flatnonzero(y == 0)
    if len(event_idx) == 0 or len(ctrl_idx) == 0:
        return {"status": "UNAVAILABLE"}
    med = train[STATE].median()
    scale = train[STATE].std().replace(0, 1.0)
    z = ((test[STATE] - med) / scale).to_numpy(float)
    z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)
    ctrl = z[ctrl_idx]
    variables = ["state_cell_dwell_h", "hazard_lag24", "burden_lag24", "rr_lag24", "hazard_delta24", "burden_delta24", "rr_delta24"]
    diffs = {v: [] for v in variables}
    for ei in event_idx:
        dist = np.sqrt(((ctrl - z[ei]) ** 2).sum(axis=1))
        take = ctrl_idx[np.argsort(dist)[:5]]
        for v in variables:
            ev = float(pd.to_numeric(test.iloc[ei][v], errors="coerce"))
            cv = pd.to_numeric(test.iloc[take][v], errors="coerce").to_numpy(float)
            cv = cv[np.isfinite(cv)]
            if np.isfinite(ev) and len(cv):
                diffs[v].append(ev - float(np.mean(cv)))
    summary = {}
    for v, arr in diffs.items():
        a = np.asarray(arr, float)
        summary[v] = {
            "matched_event_count": int(len(a)),
            "median_event_minus_control": float(np.median(a)) if len(a) else None,
            "mean_event_minus_control": float(np.mean(a)) if len(a) else None,
            "positive_fraction": float((a > 0).mean()) if len(a) else None,
        }
    return {"status": "OK", "events": int(len(event_idx)), "controls": int(len(ctrl_idx)), "matched_summary": summary}


def main(csv: Path, out: Path) -> None:
    raw = pd.read_csv(csv)
    assert len(raw) == 43848
    starts = int(((raw.entry_path == "3_to_4") & (pd.to_numeric(raw.episode_age_h, errors="coerce") == 1)).sum())
    assert starts == 169
    d = add_state_coordinates(raw)
    d[TARGET] = clean_target(d)
    year_rows = evaluate_years(d)
    offset_rows = evaluate_holdout_offsets(d)
    payload = {
        "experiment": "hydra_state_sufficiency_court_v1",
        "question": "does H+B+RR make path/timer history conditionally unnecessary?",
        "canonical_rows": len(raw),
        "canonical_h3_starts": starts,
        "state_definition": "H=hazard_score(t-1); B=LiveDeficit(t-1); RR=RecoveryWeakness_v1(t-1)-LiveDeficit(t-1)",
        "models": MODELS,
        "walk_forward": year_rows,
        "holdout_2024_72phase_offsets": offset_rows,
        "holdout_offset_summary": summarize_offsets(offset_rows),
        "matched_history_test": matched_history_test(d),
        "interpretation": {
            "state_sufficient": "supported only if history/timer deltas remain small and unstable across years and 72 offsets",
            "state_insufficient": "supported if a pre-specified history/timer block adds persistent positive AUC after conditioning on H+B+RR, especially if matched event/control states show systematic history differences",
        },
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=False))
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
