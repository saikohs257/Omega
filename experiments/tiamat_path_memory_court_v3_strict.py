from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OBS = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
HISTORY = [
    "LiveDeficit_lag1", "LiveDeficit_lag6", "LiveDeficit_lag24", "LiveDeficit_lag72",
    "ld_delta_1", "ld_delta_6", "ld_delta_24", "ld_area24", "ld_area72",
    "shock_excess24", "shock_excess72", "ld_above85_hours24", "recovery_area24",
    "hazard_peak24", "hazard_peak72",
]
CALIPERS = (0.50, 0.25, 0.15, 0.10, 0.05)
HORIZON_H = 6
MIN_SEPARATION_H = 168
NULL_N = 2000
HOLDOUT_YEAR = 2024


def numeric(d: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(d[c], errors="coerce")


def causal_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("open_time").reset_index(drop=True).copy()
    for c in OBS:
        d[c] = numeric(d, c)
    for lag in (1, 6, 24, 72):
        for c in OBS:
            d[f"{c}_lag{lag}"] = d[c].shift(lag)
    d["ld_delta_1"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(2)
    d["ld_delta_6"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(7)
    d["ld_delta_24"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(25)
    ld_prev = d["LiveDeficit"].shift(1)
    ss_prev = d["SimpleShock"].shift(1)
    d["ld_area24"] = ld_prev.rolling(24, min_periods=12).mean()
    d["ld_area72"] = ld_prev.rolling(72, min_periods=36).mean()
    d["shock_excess24"] = (ss_prev - 0.50).clip(lower=0).rolling(24, min_periods=12).sum()
    d["shock_excess72"] = (ss_prev - 0.50).clip(lower=0).rolling(72, min_periods=36).sum()
    d["ld_above85_hours24"] = (ld_prev > 0.85).rolling(24, min_periods=12).sum()
    d["recovery_area24"] = d["RecoveryWeakness_v1"].shift(1).rolling(24, min_periods=12).mean()
    d["hazard_peak24"] = d["hazard_raw"].shift(1).rolling(24, min_periods=12).max()
    d["hazard_peak72"] = d["hazard_raw"].shift(1).rolling(72, min_periods=36).max()
    return d


def future_3_to_4(d: pd.DataFrame) -> pd.Series:
    x = d[["open_time", "entry_path"]].sort_values("open_time").reset_index()
    t = x["open_time"].to_numpy()
    labels = np.zeros(len(x), dtype=np.int8)
    paths = x["entry_path"].astype(str).to_numpy()
    for i in range(len(x)):
        upper = t[i] + np.timedelta64(HORIZON_H, "h")
        j = np.searchsorted(t, upper, side="right")
        if j > i + 1:
            labels[i] = np.any(paths[i + 1:j] == "3_to_4")
    out = pd.Series(labels, index=x["index"].to_numpy())
    return out.reindex(d.index).fillna(0).astype(int)


def robust_scale(train: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    med = train[cols].median().to_numpy(float)
    q1 = train[cols].quantile(0.25).to_numpy(float)
    q3 = train[cols].quantile(0.75).to_numpy(float)
    iqr = q3 - q1
    iqr[iqr <= 1e-12] = 1.0
    return med, iqr


def make_candidates(te: pd.DataFrame, med: np.ndarray, iqr: np.ndarray) -> list[dict]:
    q = te.dropna(subset=OBS + ["target"]).copy().reset_index(drop=True)
    z = (q[OBS].to_numpy(float) - med) / iqr
    pos = np.flatnonzero(q.target.to_numpy() == 1)
    neg = np.flatnonzero(q.target.to_numpy() == 0)
    times = q.open_time.astype("int64").to_numpy()
    regimes = q["regime_30d"].astype(str).to_numpy() if "regime_30d" in q.columns else np.array([""] * len(q))
    candidates = []
    for i in pos:
        if not len(neg):
            continue
        delta = z[neg] - z[i]
        dist = np.sqrt(np.sum(delta * delta, axis=1)) / np.sqrt(len(OBS))
        sep = np.abs(times[neg] - times[i]) / 3_600_000_000_000
        valid = sep >= MIN_SEPARATION_H
        # Match within the same broad regime when available; if absent, time separation remains the guard.
        same_regime = regimes[neg] == regimes[i]
        if "regime_30d" in q.columns and np.any(valid & same_regime):
            valid = valid & same_regime
        for j_local in np.flatnonzero(valid):
            j = neg[j_local]
            candidates.append({"i": int(i), "j": int(j), "dist": float(dist[j_local])})
    candidates.sort(key=lambda r: r["dist"])
    return candidates


def greedy_pairs(te: pd.DataFrame, caliper: float, med: np.ndarray, iqr: np.ndarray) -> list[tuple[int, int, float]]:
    q = te.dropna(subset=OBS + ["target"]).copy().reset_index(drop=True)
    cands = [c for c in make_candidates(q, med, iqr) if c["dist"] <= caliper]
    used_pos: set[int] = set()
    used_neg: set[int] = set()
    pairs = []
    for c in cands:
        if c["i"] in used_pos or c["j"] in used_neg:
            continue
        used_pos.add(c["i"])
        used_neg.add(c["j"])
        pairs.append((c["i"], c["j"], c["dist"]))
    return pairs


def pairwise_auc(q: pd.DataFrame, pairs: list[tuple[int, int, float]], history: str) -> float:
    if not pairs:
        return float("nan")
    p = q[history].to_numpy(float)
    scores = []
    for i, j, _ in pairs:
        a, b = p[i], p[j]
        if np.isnan(a) or np.isnan(b):
            continue
        scores.append(1.0 if a > b else 0.0 if a < b else 0.5)
    return float(np.mean(scores)) if scores else float("nan")


def permutation_null(q: pd.DataFrame, pairs: list[tuple[int, int, float]], history: str, n: int, rng: np.random.Generator) -> dict:
    if not pairs:
        return {"mean": float("nan"), "p95": float("nan"), "p_value": float("nan"), "n": 0}
    vals = q[history].to_numpy(float)
    usable = [(i, j) for i, j, _ in pairs if np.isfinite(vals[i]) and np.isfinite(vals[j])]
    if not usable:
        return {"mean": float("nan"), "p95": float("nan"), "p_value": float("nan"), "n": 0}
    obs = []
    for _ in range(n):
        wins = 0.0
        for i, j in usable:
            if rng.integers(2) == 0:
                a, b = vals[i], vals[j]
            else:
                a, b = vals[j], vals[i]
            wins += 1.0 if a > b else 0.0 if a < b else 0.5
        obs.append(wins / len(usable))
    arr = np.asarray(obs)
    return {
        "mean": float(arr.mean()),
        "p95": float(np.quantile(arr, 0.95)),
        "p_value": float((1.0 + np.sum(arr >= 0.5 + abs(np.mean(arr) - 0.5))) / (n + 1)),
        "n": int(n),
    }


def run(csv: Path) -> dict:
    d = pd.read_csv(csv)
    req = OBS + ["open_time", "entry_path"]
    miss = [c for c in req if c not in d.columns]
    if miss:
        raise ValueError(f"missing required columns: {miss}")
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = causal_history(d)
    d["target"] = future_3_to_4(d)
    d["year"] = d.open_time.dt.year
    te = d[d.year == HOLDOUT_YEAR].copy().reset_index(drop=True)
    med, iqr = robust_scale(te, OBS)
    rng = np.random.default_rng(20260817)
    results = []
    for caliper in CALIPERS:
        pairs = greedy_pairs(te, caliper, med, iqr)
        for hist in HISTORY:
            observed = pairwise_auc(te, pairs, hist)
            null = permutation_null(te, pairs, hist, NULL_N, rng)
            results.append({
                "caliper": caliper,
                "history": hist,
                "pairs": len(pairs),
                "observed_pair_auc": observed,
                "null": null,
            })
    return {
        "experiment": "TIAMAT_PATH_MEMORY_COURT_V3_STRICT",
        "classification": "experimental/non-authoritative",
        "holdout_year": HOLDOUT_YEAR,
        "target": f"future_3_to_4_within_{HORIZON_H}h",
        "present_features": OBS,
        "history_features": HISTORY,
        "matching": {
            "method": "greedy_1to1_nearest_opposite_outcome",
            "distance": "RMS standardized IQR distance over present features",
            "same_regime_when_available": True,
            "minimum_temporal_separation_h": MIN_SEPARATION_H,
            "calipers": CALIPERS,
        },
        "null": {"type": "within_pair_outcome_orientation_swap", "n": NULL_N, "seed": 20260817},
        "forbidden_predictors": ["entry_path", "episode_type", "duration_bucket", "Crash72"],
        "results": results,
    }


def main(csv: Path, out: Path) -> None:
    payload = run(csv)
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
