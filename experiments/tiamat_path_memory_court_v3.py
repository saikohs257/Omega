from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

OBS = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
HISTORY = [
    "LiveDeficit_lag1", "LiveDeficit_lag6", "LiveDeficit_lag24", "LiveDeficit_lag72",
    "ld_delta_1", "ld_delta_6", "ld_delta_24", "ld_area24", "ld_area72",
    "shock_excess24", "shock_excess72", "ld_above85_hours24", "recovery_area24",
    "hazard_peak24", "hazard_peak72",
]
DISCOVERY_YEARS = (2021, 2022, 2023)
HOLDOUT_YEAR = 2024


def num(d: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(d[c], errors="coerce")


def causal_history(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("open_time").reset_index(drop=True).copy()
    for c in OBS:
        d[c] = num(d, c)
    for lag in (1, 6, 24, 72):
        for c in ("LiveDeficit", "SimpleShock", "RecoveryWeakness_v1", "hazard_raw"):
            d[f"{c}_lag{lag}"] = d[c].shift(lag)
    d["ld_delta_1"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(2)
    d["ld_delta_6"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(7)
    d["ld_delta_24"] = d["LiveDeficit"].shift(1) - d["LiveDeficit"].shift(25)
    ld = d["LiveDeficit"].shift(1)
    ss = d["SimpleShock"].shift(1)
    d["ld_area24"] = ld.rolling(24, min_periods=12).mean()
    d["ld_area72"] = ld.rolling(72, min_periods=36).mean()
    d["shock_excess24"] = (ss - 0.50).clip(lower=0).rolling(24, min_periods=12).sum()
    d["shock_excess72"] = (ss - 0.50).clip(lower=0).rolling(72, min_periods=36).sum()
    d["ld_above85_hours24"] = (ld > 0.85).rolling(24, min_periods=12).sum()
    d["recovery_area24"] = d["RecoveryWeakness_v1"].shift(1).rolling(24, min_periods=12).mean()
    d["hazard_peak24"] = d["hazard_raw"].shift(1).rolling(24, min_periods=12).max()
    d["hazard_peak72"] = d["hazard_raw"].shift(1).rolling(72, min_periods=36).max()
    return d


def future_target(d: pd.DataFrame, horizon_h: int) -> pd.Series:
    x = d[["open_time", "entry_path"]].copy().sort_values("open_time")
    t = x["open_time"].to_numpy()
    labels = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        j = np.searchsorted(t, t[i] + np.timedelta64(horizon_h, "h"), side="right")
        if j > i + 1:
            labels[i] = int(np.any(x["entry_path"].iloc[i+1:j].eq("3_to_4").to_numpy()))
    return pd.Series(labels, index=d.index)


def robust_scale(train: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    med = train[OBS].median().to_numpy(dtype=float)
    q1 = train[OBS].quantile(0.25).to_numpy(dtype=float)
    q3 = train[OBS].quantile(0.75).to_numpy(dtype=float)
    scale = np.maximum(q3 - q1, 1e-9)
    return med, scale


def make_pairs(te: pd.DataFrame, med: np.ndarray, scale: np.ndarray, caliper: float) -> list[tuple[int,int,float]]:
    q = te.dropna(subset=OBS+["target"]).copy().reset_index(drop=True)
    z = (q[OBS].to_numpy(dtype=float) - med) / scale
    times = q.open_time.to_numpy()
    used: set[int] = set()
    pairs = []
    # Greedy nearest-neighbour 1:1 matching. Require opposite future outcomes,
    # non-adjacent timestamps, and small max-coordinate distance.
    order = np.argsort(times)
    candidates = []
    for ai in order:
        if ai in used:
            continue
        best = None
        for bj in order:
            if bj == ai or bj in used or q.target.iloc[ai] == q.target.iloc[bj]:
                continue
            hours = abs((times[ai] - times[bj]) / np.timedelta64(1, "h"))
            if hours < 168:
                continue
            dist = float(np.max(np.abs(z[ai] - z[bj])))
            if dist <= caliper and (best is None or dist < best[0]):
                best = (dist, bj)
        if best is not None:
            dist, bj = best
            used.add(ai); used.add(bj)
            candidates.append((ai, bj, dist))
    return candidates, q


def paired_history_score(q: pd.DataFrame, pairs: list[tuple[int,int,float]], candidate: str) -> float:
    if not pairs:
        return float("nan")
    correct = 0; total = 0
    for ai, bi, _ in pairs:
        ya, yb = int(q.target.iloc[ai]), int(q.target.iloc[bi])
        ha, hb = q[candidate].iloc[ai], q[candidate].iloc[bi]
        if pd.isna(ha) or pd.isna(hb) or ha == hb:
            continue
        # score = probability that larger history value belongs to positive future target
        if ya == 1 and yb == 0:
            correct += int(ha > hb) + 0.5 * int(ha == hb)
            total += 1
        elif yb == 1 and ya == 0:
            correct += int(hb > ha) + 0.5 * int(ha == hb)
            total += 1
    return float(correct / total) if total else float("nan")


def permutation_null(q: pd.DataFrame, pairs: list[tuple[int,int,float]], candidate: str, n: int=1000, seed: int=17) -> dict:
    if not pairs:
        return {"observed": float("nan"), "null_mean": float("nan"), "null_p95": float("nan"), "p_perm": float("nan"), "n_pairs": 0}
    observed = paired_history_score(q, pairs, candidate)
    rng = np.random.default_rng(seed)
    vals = q[candidate].to_numpy(copy=True)
    null = []
    pair_indices = np.array([[a,b] for a,b,_ in pairs], dtype=int)
    for _ in range(n):
        qp = q.copy()
        perm = vals.copy()
        for a,b in pair_indices:
            if rng.random() < 0.5:
                perm[a], perm[b] = perm[b], perm[a]
        qp[candidate] = perm
        null.append(paired_history_score(qp, pairs, candidate))
    null = np.asarray(null, dtype=float)
    return {
        "observed": float(observed),
        "null_mean": float(np.nanmean(null)),
        "null_p95": float(np.nanquantile(null, 0.95)),
        "p_perm": float((1 + np.sum(null >= observed)) / (1 + len(null))),
        "n_pairs": int(len(pairs)),
    }


def run(csv: Path, out: Path) -> None:
    d = pd.read_csv(csv)
    req = OBS + ["open_time", "entry_path"]
    missing = [c for c in req if c not in d.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d = causal_history(d)
    d["year"] = d.open_time.dt.year
    x = d.copy()
    x["target"] = future_target(x, 6)

    results = {}
    # Fit matching geometry from pre-holdout discovery only.
    train_geo = x[x.year.isin(DISCOVERY_YEARS)].dropna(subset=OBS)
    med, scale = robust_scale(train_geo)
    for caliper in (0.50, 0.25, 0.15, 0.10, 0.05):
        te = x[x.year == HOLDOUT_YEAR].copy()
        pairs, q = make_pairs(te, med, scale, caliper)
        rows = []
        for c in HISTORY:
            null = permutation_null(q, pairs, c, n=1000)
            rows.append({"history": c, **null})
        results[str(caliper)] = {
            "caliper": caliper,
            "pairs": int(len(pairs)),
            "median_max_z_distance": float(np.median([p[2] for p in pairs])) if pairs else float("nan"),
            "history": rows,
        }
    payload = {
        "experiment": "TIAMAT_PATH_MEMORY_COURT_V3",
        "classification": "experimental/non-authoritative",
        "target": "future_3_to_4_within_6h",
        "present_state": OBS,
        "forbidden": ["entry_path", "episode_type", "duration_bucket", "Crash72"],
        "matching": "1:1 greedy nearest-neighbour, opposite future target, >=168h temporal separation, max standardized coordinate distance <= caliper",
        "scale_fit": "2021-2023 discovery only; IQR scale",
        "calipers": [0.50,0.25,0.15,0.10,0.05],
        "results": results,
        "interpretation": "Evidence for path memory requires a history score materially above 0.5 after increasingly tight present-state matching and a permutation p-value below 0.05; otherwise classify as present-state proxy.",
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); run(a.csv,a.out)
