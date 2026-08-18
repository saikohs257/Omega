from __future__ import annotations

import argparse
import json
from pathlib import Path

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
CORE_MEMORY = ["ld_lag24"]
HORIZON_H = 6
MIN_SEPARATION_H = 168
CALIPER = 0.05
HOLDOUT_YEAR = 2024
PURGE_H = HORIZON_H


def metric(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-7, 1 - 1e-7)
    return {
        "n": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()),
        "auc": float(roc_auc_score(y, p)) if np.unique(y).size == 2 else None,
        "pr_auc": float(average_precision_score(y, p)) if y.sum() else None,
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
    }


def make_model(cols: list[str]):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=2500, class_weight="balanced", C=0.5, solver="liblinear"),
    )


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True, errors="raise")
    d = d.sort_values("open_time").reset_index(drop=True)
    for c in OBS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    ld = d["LiveDeficit"]
    ss = d["SimpleShock"]
    rw = d["RecoveryWeakness_v1"]
    hz = d["hazard_raw"]
    ld1, ss1, rw1, hz1 = ld.shift(1), ss.shift(1), rw.shift(1), hz.shift(1)

    d[RR] = rw1 - ld1
    d["ld_lag1"] = ld1
    d["ld_lag6"] = ld.shift(6)
    d["ld_lag24"] = ld.shift(24)
    d["ld_lag72"] = ld.shift(72)
    d["ld_delta1"] = ld1 - ld.shift(2)
    d["ld_delta6"] = ld1 - ld.shift(7)
    d["ld_delta24"] = ld1 - ld.shift(25)
    d["ld_area24"] = ld1.rolling(24, min_periods=12).mean()
    d["ld_area72"] = ld1.rolling(72, min_periods=36).mean()
    d["shock_excess24"] = (ss1 - 0.50).clip(lower=0).rolling(24, min_periods=12).sum()
    d["shock_excess72"] = (ss1 - 0.50).clip(lower=0).rolling(72, min_periods=36).sum()
    d["ld_above85_hours24"] = (ld1 > 0.85).rolling(24, min_periods=12).sum()
    d["recovery_area24"] = rw1.rolling(24, min_periods=12).mean()
    d["hazard_peak24"] = hz1.rolling(24, min_periods=12).max()
    d["hazard_peak72"] = hz1.rolling(72, min_periods=36).max()

    x = d[["open_time", "entry_path"]].copy()
    t = x["open_time"].to_numpy(dtype="datetime64[ns]")
    p = x["entry_path"].astype(str).to_numpy()
    y = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        j = np.searchsorted(t, t[i] + np.timedelta64(HORIZON_H, "h"), side="right")
        if j > i + 1:
            y[i] = int(np.any(p[i + 1:j] == "3_to_4"))
    d["target"] = y
    return d


def purge(train: pd.DataFrame, test_start: pd.Timestamp) -> pd.DataFrame:
    return train[train.open_time < test_start - pd.Timedelta(hours=PURGE_H)]


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    m = make_model(cols)
    m.fit(train[cols], train.target)
    return m.predict_proba(test[cols])[:, 1]


def model_ladder(d: pd.DataFrame) -> dict:
    state4 = OBS
    state5 = OBS + [RR]
    configs = {
        "state4": state4,
        "state4_plus_lag24": OBS + ["ld_lag24"],
        "state4_plus_lag24_rr": OBS + ["ld_lag24", RR],
        "state4_plus_all_history": OBS + HISTORY,
        "state5_plus_all_history": state5 + HISTORY,
    }
    years = [2021, 2022, 2023]
    out = {"holdout_2024": {}, "walk_forward": {name: [] for name in configs}}
    hold = d[d.open_time.dt.year == HOLDOUT_YEAR]
    train = purge(d[d.open_time.dt.year < HOLDOUT_YEAR], hold.open_time.min())
    for name, cols in configs.items():
        out["holdout_2024"][name] = metric(hold.target.to_numpy(), fit_predict(train, hold, cols))
        for year in years:
            test = d[d.open_time.dt.year == year]
            tr = purge(d[d.open_time.dt.year < year], test.open_time.min())
            if len(tr) < 200 or tr.target.nunique() < 2:
                continue
            out["walk_forward"][name].append({"year": year, "metrics": metric(test.target.to_numpy(), fit_predict(tr, test, cols))})

    base = out["holdout_2024"]["state4"]["auc"]
    full = out["holdout_2024"]["state4_plus_all_history"]["auc"]
    lag = out["holdout_2024"]["state4_plus_lag24"]["auc"]
    out["closure"] = {
        "baseline_auc": base,
        "full_history_auc": full,
        "lag24_auc": lag,
        "lag24_share_of_full_history_auc_gain": float((lag - base) / (full - base)) if full != base else None,
        "interpretation_rule": "A lag24 share near 1 means most residual history information is captured by one 24h memory coordinate; substantially below 1 implies richer path state.",
    }
    return out


def scale_from_discovery(train: pd.DataFrame, cols: list[str]):
    q1 = train[cols].quantile(0.25).to_numpy(float)
    q3 = train[cols].quantile(0.75).to_numpy(float)
    med = train[cols].median().to_numpy(float)
    iqr = q3 - q1
    iqr[iqr <= 1e-12] = 1.0
    return med, iqr


def pair_state(d: pd.DataFrame, cols: list[str]) -> list[tuple[int, int, float]]:
    train = d[d.open_time.dt.year < HOLDOUT_YEAR].dropna(subset=cols)
    hold = d[d.open_time.dt.year == HOLDOUT_YEAR].dropna(subset=cols + ["target"]).reset_index(drop=True)
    med, iqr = scale_from_discovery(train, cols)
    z = (hold[cols].to_numpy(float) - med) / iqr
    times = hold.open_time.to_numpy(dtype="datetime64[ns]")
    pos = np.flatnonzero(hold.target.to_numpy() == 1)
    neg = np.flatnonzero(hold.target.to_numpy() == 0)
    cand = []
    for i in pos:
        gap = np.abs((times[neg] - times[i]) / np.timedelta64(1, "h"))
        dist = np.sqrt(((z[neg] - z[i]) ** 2).sum(axis=1)) / np.sqrt(len(cols))
        for k in np.flatnonzero(gap >= MIN_SEPARATION_H):
            if dist[k] <= CALIPER:
                cand.append((int(i), int(neg[k]), float(dist[k])))
    cand.sort(key=lambda a: a[2])
    used_i, used_j = set(), set()
    out = []
    for i, j, dist in cand:
        if i in used_i or j in used_j:
            continue
        used_i.add(i)
        used_j.add(j)
        out.append((i, j, dist))
    return out


def pair_orientation(hold: pd.DataFrame, pairs, feature: str) -> float | None:
    v = pd.to_numeric(hold[feature], errors="coerce").to_numpy(float)
    vals = []
    for i, j, _ in pairs:
        if np.isfinite(v[i]) and np.isfinite(v[j]):
            vals.append(1.0 if v[i] > v[j] else 0.0 if v[i] < v[j] else 0.5)
    return float(np.mean(vals)) if vals else None


def matching_tests(d: pd.DataFrame) -> dict:
    hold = d[d.open_time.dt.year == HOLDOUT_YEAR].dropna(subset=OBS + ["target"]).reset_index(drop=True)
    state4_pairs = pair_state(d, OBS)
    state4_lag24_pairs = pair_state(d, OBS + ["ld_lag24"])
    state4_lag24_rr_pairs = pair_state(d, OBS + ["ld_lag24", RR])

    residuals = {}
    for label, pairs, matched in [
        ("state4", state4_pairs, OBS),
        ("state4_plus_lag24", state4_lag24_pairs, OBS + ["ld_lag24"]),
        ("state4_plus_lag24_rr", state4_lag24_rr_pairs, OBS + ["ld_lag24", RR]),
    ]:
        excluded = set(matched)
        hist = [h for h in HISTORY if h not in excluded]
        residuals[label] = {
            "pairs": len(pairs),
            "median_distance": float(np.median([x[2] for x in pairs])) if pairs else None,
            "history_orientation": {h: pair_orientation(hold, pairs, h) for h in hist},
        }

    return {
        "holdout_year": HOLDOUT_YEAR,
        "min_separation_h": MIN_SEPARATION_H,
        "caliper": CALIPER,
        "scale_source": "2020-2023 only",
        "pairs": {
            "state4": len(state4_pairs),
            "state4_plus_lag24": len(state4_lag24_pairs),
            "state4_plus_lag24_rr": len(state4_lag24_rr_pairs),
        },
        "lag24_orientation_after_state4": pair_orientation(hold, state4_pairs, "ld_lag24"),
        "delta24_orientation_after_state4": pair_orientation(hold, state4_pairs, "ld_delta24"),
        "residuals": residuals,
    }


def main(path: Path, out: Path):
    d = pd.read_csv(path)
    required = OBS + ["open_time", "entry_path", "episode_age_h"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    if len(d) != 43848:
        raise SystemExit(f"Canonical row count mismatch: {len(d)}")
    d = add_features(d)
    starts = int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum())
    if starts != 169:
        raise SystemExit(f"Canonical start count mismatch: {starts}")

    payload = {
        "experiment": "TIAMAT_STATE_COMPLETION_COURT_V3_MINIMAL_MEMORY",
        "classification": "experimental/non-authoritative",
        "question": "Does one 24h memory coordinate close the residual history signal after matching the present observable state?",
        "canonical": {"rows": len(d), "h3_starts": starts, "holdout_year": HOLDOUT_YEAR},
        "state": OBS,
        "candidate_memory": "ld_lag24",
        "secondary_memory": ["ld_area24", "ld_delta24", "ld_lag6", "ld_lag72"],
        "target": "future_3_to_4_within_6h",
        "controls": {"holdout_geometry_frozen": True, "discovery_years": [2020, 2021, 2022, 2023], "purge_hours": PURGE_H, "pair_separation_hours": MIN_SEPARATION_H},
        "model_ladder": model_ladder(d),
        "matching": matching_tests(d),
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=False))
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    main(a.csv, a.out)
