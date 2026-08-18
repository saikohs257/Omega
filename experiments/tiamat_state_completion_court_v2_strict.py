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

OBS = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
RR = "rr_recovery_minus_burden"
HISTORY = [
    "ld_lag1", "ld_lag6", "ld_lag24", "ld_lag72",
    "ld_delta1", "ld_delta6", "ld_delta24",
    "ld_area24", "ld_area72",
    "shock_excess24", "shock_excess72",
    "ld_above85_hours24", "recovery_area24",
    "hazard_peak24", "hazard_peak72",
]
HORIZON_H = 6
MIN_SEPARATION_H = 168
CALIPER = 0.05
NULL_N = 2000
HOLDOUT_YEAR = 2024
DISCOVERY_YEARS = (2020, 2021, 2022, 2023)
PURGE_H = HORIZON_H
SEED = 20260818


def numeric(d: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(d[c], errors="coerce")


def add_causal_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("open_time").reset_index(drop=True).copy()
    for c in OBS:
        d[c] = numeric(d, c)

    ld = d["LiveDeficit"]
    ss = d["SimpleShock"]
    rw = d["RecoveryWeakness_v1"]
    hz = d["hazard_raw"]

    # Every derived predictor uses only information strictly before t.
    ld_prev = ld.shift(1)
    ss_prev = ss.shift(1)
    rw_prev = rw.shift(1)
    hz_prev = hz.shift(1)

    d["rr_recovery_minus_burden"] = rw_prev - ld_prev
    d["ld_lag1"] = ld_prev
    d["ld_lag6"] = ld.shift(6)
    d["ld_lag24"] = ld.shift(24)
    d["ld_lag72"] = ld.shift(72)
    d["ld_delta1"] = ld_prev - ld.shift(2)
    d["ld_delta6"] = ld_prev - ld.shift(7)
    d["ld_delta24"] = ld_prev - ld.shift(25)
    d["ld_area24"] = ld_prev.rolling(24, min_periods=12).mean()
    d["ld_area72"] = ld_prev.rolling(72, min_periods=36).mean()
    d["shock_excess24"] = (ss_prev - 0.50).clip(lower=0).rolling(24, min_periods=12).sum()
    d["shock_excess72"] = (ss_prev - 0.50).clip(lower=0).rolling(72, min_periods=36).sum()
    d["ld_above85_hours24"] = (ld_prev > 0.85).rolling(24, min_periods=12).sum()
    d["recovery_area24"] = rw_prev.rolling(24, min_periods=12).mean()
    d["hazard_peak24"] = hz_prev.rolling(24, min_periods=12).max()
    d["hazard_peak72"] = hz_prev.rolling(72, min_periods=36).max()

    return d


def future_3_to_4(d: pd.DataFrame) -> pd.Series:
    x = d[["open_time", "entry_path"]].sort_values("open_time").reset_index()
    t = x["open_time"].to_numpy(dtype="datetime64[ns]")
    p = x["entry_path"].astype(str).to_numpy()
    y = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        j = np.searchsorted(t, t[i] + np.timedelta64(HORIZON_H, "h"), side="right")
        if j > i + 1:
            y[i] = int(np.any(p[i + 1 : j] == "3_to_4"))
    return pd.Series(y, index=x["index"].to_numpy()).reindex(d.index).fillna(0).astype(int)


def robust_scale(train: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    med = train[cols].median().to_numpy(float)
    q1 = train[cols].quantile(0.25).to_numpy(float)
    q3 = train[cols].quantile(0.75).to_numpy(float)
    iqr = q3 - q1
    iqr[iqr <= 1e-12] = 1.0
    return med, iqr


def match_pairs(q: pd.DataFrame, cols: list[str], med: np.ndarray, iqr: np.ndarray) -> list[tuple[int, int, float]]:
    q = q.dropna(subset=cols + ["target"]).reset_index(drop=True)
    z = (q[cols].to_numpy(float) - med) / iqr
    times = q["open_time"].to_numpy(dtype="datetime64[ns]")
    pos = np.flatnonzero(q["target"].to_numpy() == 1)
    neg = np.flatnonzero(q["target"].to_numpy() == 0)
    cand: list[tuple[int, int, float]] = []
    for i in pos:
        if not len(neg):
            continue
        delta = z[neg] - z[i]
        dist = np.sqrt(np.sum(delta * delta, axis=1)) / np.sqrt(len(cols))
        gap_h = np.abs((times[neg] - times[i]) / np.timedelta64(1, "h"))
        valid = gap_h >= MIN_SEPARATION_H
        for k in np.flatnonzero(valid):
            cand.append((int(i), int(neg[k]), float(dist[k])))
    cand.sort(key=lambda x: x[2])
    used_pos: set[int] = set()
    used_neg: set[int] = set()
    pairs: list[tuple[int, int, float]] = []
    for i, j, dist in cand:
        if dist > CALIPER:
            break
        if i in used_pos or j in used_neg:
            continue
        used_pos.add(i)
        used_neg.add(j)
        pairs.append((i, j, dist))
    return pairs


def pair_orientation(q: pd.DataFrame, pairs: list[tuple[int, int, float]], feature: str) -> float | None:
    if not pairs:
        return None
    v = numeric(q, feature).to_numpy(float)
    usable = [(i, j) for i, j, _ in pairs if np.isfinite(v[i]) and np.isfinite(v[j])]
    if not usable:
        return None
    wins = [1.0 if v[i] > v[j] else 0.0 if v[i] < v[j] else 0.5 for i, j in usable]
    return float(np.mean(wins))


def permutation_p(q: pd.DataFrame, pairs: list[tuple[int, int, float]], feature: str, observed: float | None) -> float | None:
    if observed is None or not pairs:
        return None
    v = numeric(q, feature).to_numpy(float)
    usable = [(i, j) for i, j, _ in pairs if np.isfinite(v[i]) and np.isfinite(v[j])]
    if not usable:
        return None
    rng = np.random.default_rng(SEED)
    null = np.empty(NULL_N, dtype=float)
    for k in range(NULL_N):
        wins = 0.0
        for i, j in usable:
            if rng.integers(2) == 0:
                a, b = v[i], v[j]
            else:
                a, b = v[j], v[i]
            wins += 1.0 if a > b else 0.0 if a < b else 0.5
        null[k] = wins / len(usable)
    p = (1.0 + np.sum(np.abs(null - 0.5) >= abs(observed - 0.5))) / (NULL_N + 1.0)
    return float(p)


def metric(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-7, 1 - 1e-7)
    two = np.unique(y).size == 2
    return {
        "n": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()),
        "auc": float(roc_auc_score(y, p)) if two else None,
        "pr_auc": float(average_precision_score(y, p)) if y.sum() else None,
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "mean_prediction": float(p.mean()),
    }


def make_model(cols: list[str]):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2500, class_weight="balanced", C=0.5, solver="liblinear"),
    )


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    m = make_model(cols)
    m.fit(train[cols].astype(float), train["target"].astype(int))
    return m.predict_proba(test[cols].astype(float))[:, 1]


def purge_train(train: pd.DataFrame, test_start: pd.Timestamp) -> pd.DataFrame:
    cutoff = test_start - pd.Timedelta(hours=PURGE_H)
    return train[train["open_time"] < cutoff].copy()


def walkforward(d: pd.DataFrame, cols: list[str]) -> list[dict]:
    out = []
    for year in (2021, 2022, 2023):
        te = d[d.open_time.dt.year == year].copy()
        if te.empty:
            continue
        tr = purge_train(d[d.open_time.dt.year < year], te.open_time.min())
        if len(tr) < 200 or tr.target.nunique() < 2:
            continue
        out.append({"year": year, "metrics": metric(te.target.to_numpy(), fit_predict(tr, te, cols))})
    return out


def compare_models(d: pd.DataFrame) -> dict:
    state4 = OBS
    state5 = OBS + [RR]
    state4_hist = OBS + HISTORY
    state5_hist = OBS + [RR] + HISTORY
    configs = {
        "state4": state4,
        "state5_rr": state5,
        "state4_plus_history": state4_hist,
        "state5_rr_plus_history": state5_hist,
    }
    hold = d[d.open_time.dt.year == HOLDOUT_YEAR].copy()
    tr = purge_train(d[d.open_time.dt.year < HOLDOUT_YEAR], hold.open_time.min())
    return {
        "holdout": {name: metric(hold.target.to_numpy(), fit_predict(tr, hold, cols)) for name, cols in configs.items()},
        "walk_forward": {name: walkforward(d, cols) for name, cols in configs.items()},
        "feature_sets": configs,
    }


def corrected_state_matching(d: pd.DataFrame) -> dict:
    hold = d[d.open_time.dt.year == HOLDOUT_YEAR].copy().reset_index(drop=True)
    train = d[d.open_time.dt.year < HOLDOUT_YEAR].copy()
    results = []
    state_sets = [
        ("state4", OBS),
        ("state5_rr", OBS + [RR]),
    ]
    for name, cols in state_sets:
        med, iqr = robust_scale(train.dropna(subset=cols), cols)
        q = hold.dropna(subset=cols + ["target"]).copy().reset_index(drop=True)
        pairs = match_pairs(q, cols, med, iqr)
        row = {
            "state": name,
            "matching_features": cols,
            "pairs": int(len(pairs)),
            "median_pair_distance": float(np.median([x[2] for x in pairs])) if pairs else None,
            "max_pair_distance": float(np.max([x[2] for x in pairs])) if pairs else None,
            "history": {},
        }
        for hist in HISTORY:
            obs = pair_orientation(q, pairs, hist)
            row["history"][hist] = {
                "pair_orientation_auc": obs,
                "permutation_p_two_sided": permutation_p(q, pairs, hist, obs),
            }
        results.append(row)
    return {
        "holdout_year": HOLDOUT_YEAR,
        "caliper": CALIPER,
        "minimum_temporal_separation_h": MIN_SEPARATION_H,
        "scale_source": "2020-2023 only; median/IQR frozen before 2024",
        "results": results,
    }


def main(csv: Path, out: Path) -> None:
    raw = pd.read_csv(csv)
    required = OBS + ["open_time", "entry_path", "episode_age_h"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    if len(raw) != 43848:
        raise SystemExit(f"Canonical row count mismatch: {len(raw)}")

    d = add_causal_features(raw)
    d["target"] = future_3_to_4(d)
    d["year"] = d.open_time.dt.year
    starts = int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum())
    if starts != 169:
        raise SystemExit(f"Canonical start count mismatch: {starts}")

    payload = {
        "experiment": "TIAMAT_STATE_COMPLETION_COURT_V2_STRICT",
        "classification": "experimental/non-authoritative",
        "question": "After freezing present-state geometry from 2020-2023, does history still discriminate 3-to-4 transitions on untouched 2024?",
        "canonical": {
            "rows": int(len(raw)),
            "h3_starts": starts,
            "holdout_year": HOLDOUT_YEAR,
        },
        "target": f"future_3_to_4_within_{HORIZON_H}h",
        "state_sets": {
            "state4": OBS,
            "state5_rr": OBS + [RR],
            "rr_note": "RR is a derived coordinate from lagged RecoveryWeakness and LiveDeficit; it is not treated as an independent canonical variable.",
        },
        "history_features": HISTORY,
        "matching": corrected_state_matching(d),
        "nested_temporal_models": compare_models(d),
        "forbidden_predictors": ["entry_path", "episode_type", "duration_bucket", "Crash72"],
        "controls": {
            "holdout_scaling_used": False,
            "history_selection_on_holdout": False,
            "target_peek": False,
            "purge_hours": PURGE_H,
            "minimum_pair_separation_hours": MIN_SEPARATION_H,
            "seed": SEED,
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
