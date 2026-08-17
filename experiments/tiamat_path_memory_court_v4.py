from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE = ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]
DISCOVERY_YEARS = (2020, 2021, 2022)
VALIDATION_YEAR = 2023
HOLDOUT_YEAR = 2024
HORIZON_H = 6
MIN_SEP_H = 168
CALIPER = 0.25


def target(d: pd.DataFrame) -> pd.Series:
    x = d.sort_values("open_time").reset_index(drop=True)
    t = x.open_time.to_numpy()
    p = x.entry_path.astype(str).to_numpy()
    y = np.zeros(len(x), dtype=np.int8)
    for i in range(len(x)):
        j = np.searchsorted(t, t[i] + np.timedelta64(HORIZON_H, "h"), side="right")
        if j > i + 1:
            y[i] = int(np.any(p[i + 1:j] == "3_to_4"))
    return pd.Series(y, index=x.index)


def causal_features(d: pd.DataFrame) -> pd.DataFrame:
    x = d.sort_values("open_time").reset_index(drop=True).copy()
    for c in BASE:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    ld = x.LiveDeficit
    sh = x.SimpleShock
    rw = x.RecoveryWeakness_v1
    hz = x.hazard_raw

    # Every history variable is strictly pre-t: shift(1) before rolling/lagging.
    ld1 = ld.shift(1)
    sh1 = sh.shift(1)
    rw1 = rw.shift(1)
    hz1 = hz.shift(1)

    out = {
        "ld_lag1": ld.shift(1),
        "ld_lag6": ld.shift(6),
        "ld_lag24": ld.shift(24),
        "ld_lag72": ld.shift(72),
        "ld_delta1": ld.shift(1) - ld.shift(2),
        "ld_delta6": ld.shift(1) - ld.shift(7),
        "ld_delta24": ld.shift(1) - ld.shift(25),
        "ld_area6": ld1.rolling(6, min_periods=3).mean(),
        "ld_area24": ld1.rolling(24, min_periods=12).mean(),
        "ld_area72": ld1.rolling(72, min_periods=36).mean(),
        "shock_excess24": (sh1 - 0.50).clip(lower=0).rolling(24, min_periods=12).sum(),
        "shock_excess72": (sh1 - 0.50).clip(lower=0).rolling(72, min_periods=36).sum(),
        "ld_above85_hours24": (ld1 > 0.85).rolling(24, min_periods=12).sum(),
        "ld_above70_hours24": (ld1 > 0.70).rolling(24, min_periods=12).sum(),
        "recovery_area24": rw1.rolling(24, min_periods=12).mean(),
        "hazard_peak24": hz1.rolling(24, min_periods=12).max(),
        "hazard_peak72": hz1.rolling(72, min_periods=36).max(),
        "ld_peak24": ld1.rolling(24, min_periods=12).max(),
        "ld_peak72": ld1.rolling(72, min_periods=36).max(),
        "shock_peak24": sh1.rolling(24, min_periods=12).max(),
        "shock_peak72": sh1.rolling(72, min_periods=36).max(),
        "recovery_peak24": rw1.rolling(24, min_periods=12).max(),
        "recent_excursions48": (ld1 > 0.70).astype(float).diff().fillna(0).gt(0).rolling(48, min_periods=24).sum(),
    }
    for name, s in out.items():
        x[name] = s
    x["target"] = target(x)
    x["year"] = x.open_time.dt.year
    return x


def fit_geometry(train: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    med = train[BASE].median().to_numpy(float)
    iqr = (train[BASE].quantile(0.75) - train[BASE].quantile(0.25)).to_numpy(float)
    iqr[iqr <= 1e-12] = 1.0
    return med, iqr


def match_pairs(q: pd.DataFrame, med: np.ndarray, iqr: np.ndarray) -> list[tuple[int, int]]:
    q = q.dropna(subset=BASE + ["target"]).reset_index(drop=True)
    z = (q[BASE].to_numpy(float) - med) / iqr
    pos = np.flatnonzero(q.target.to_numpy() == 1)
    neg = np.flatnonzero(q.target.to_numpy() == 0)
    ts = q.open_time.to_numpy(dtype="datetime64[ns]")
    candidates = []
    for i in pos:
        dist = np.sqrt(((z[neg] - z[i]) ** 2).mean(1))
        sep = np.abs((ts[neg] - ts[i]) / np.timedelta64(1, "h"))
        for k in np.flatnonzero(sep >= MIN_SEP_H):
            if dist[k] <= CALIPER:
                candidates.append((float(dist[k]), int(i), int(neg[k])))
    candidates.sort(key=lambda t: t[0])
    used: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for _, a, b in candidates:
        if a in used or b in used:
            continue
        used.add(a)
        used.add(b)
        pairs.append((a, b))
    return pairs, q


def orient_direction(q: pd.DataFrame, pairs: list[tuple[int, int]], candidate: str) -> int:
    deltas = []
    vals = q[candidate].to_numpy(float)
    y = q.target.to_numpy(int)
    for a, b in pairs:
        if not np.isfinite(vals[a]) or not np.isfinite(vals[b]):
            continue
        # Pair is always positive-vs-negative; signed difference is positive
        # when history value is larger on the future-positive member.
        if y[a] == 1:
            deltas.append(vals[a] - vals[b])
        else:
            deltas.append(vals[b] - vals[a])
    if not deltas:
        return 0
    m = float(np.nanmean(deltas))
    return 1 if m >= 0 else -1


def paired_score(q: pd.DataFrame, pairs: list[tuple[int, int]], candidate: str, direction: int) -> tuple[float, int]:
    if direction == 0:
        return float("nan"), 0
    vals = q[candidate].to_numpy(float)
    y = q.target.to_numpy(int)
    correct = 0.0
    total = 0
    for a, b in pairs:
        if not np.isfinite(vals[a]) or not np.isfinite(vals[b]) or vals[a] == vals[b]:
            continue
        if y[a] == 1:
            delta = direction * (vals[a] - vals[b])
        else:
            delta = direction * (vals[b] - vals[a])
        correct += 1.0 if delta > 0 else 0.0
        total += 1
    return (correct / total if total else float("nan"), total)


def permutation_p(q: pd.DataFrame, pairs: list[tuple[int, int]], candidate: str, direction: int, n: int = 2000, seed: int = 17) -> float:
    observed, _ = paired_score(q, pairs, candidate, direction)
    if not np.isfinite(observed):
        return float("nan")
    vals = q[candidate].to_numpy(float).copy()
    rng = np.random.default_rng(seed)
    extreme = 0
    valid = 0
    for _ in range(n):
        perm = vals.copy()
        for a, b in pairs:
            if rng.random() < 0.5:
                perm[a], perm[b] = perm[b], perm[a]
        q2 = q.copy()
        q2[candidate] = perm
        score, cnt = paired_score(q2, pairs, candidate, direction)
        if cnt:
            valid += 1
            extreme += int(score >= observed)
    return float((1 + extreme) / (1 + valid)) if valid else float("nan")


def main(inp: str, out: str) -> None:
    x = pd.read_csv(inp)
    x.open_time = pd.to_datetime(x.open_time, utc=True)
    x = causal_features(x)

    geometry_train = x[x.year.isin(DISCOVERY_YEARS)].dropna(subset=BASE)
    med, iqr = fit_geometry(geometry_train)

    candidates = [c for c in x.columns if c in {
        "ld_lag1", "ld_lag6", "ld_lag24", "ld_lag72", "ld_delta1", "ld_delta6", "ld_delta24",
        "ld_area6", "ld_area24", "ld_area72", "shock_excess24", "shock_excess72",
        "ld_above85_hours24", "ld_above70_hours24", "recovery_area24", "hazard_peak24", "hazard_peak72",
        "ld_peak24", "ld_peak72", "shock_peak24", "shock_peak72", "recovery_peak24", "recent_excursions48"
    }]

    # Direction is learned only from 2020-2022 and is then frozen.
    disc = x[x.year.isin(DISCOVERY_YEARS)].dropna(subset=BASE + ["target"])
    all_pairs = []
    direction_rows = []
    for year in DISCOVERY_YEARS:
        p, q = match_pairs(x[x.year == year], med, iqr)
        all_pairs.extend([(year, a, b) for a, b in p])
    for c in candidates:
        # Reassemble discovery pairs within each year so q indices are local.
        rows = []
        deltas = []
        for year in DISCOVERY_YEARS:
            p, q = match_pairs(x[x.year == year], med, iqr)
            vals = q[c].to_numpy(float)
            y = q.target.to_numpy(int)
            for a, b in p:
                if not np.isfinite(vals[a]) or not np.isfinite(vals[b]) or vals[a] == vals[b]:
                    continue
                d = vals[a] - vals[b] if y[a] == 1 else vals[b] - vals[a]
                deltas.append(float(d))
            s, n = paired_score(q, p, c, 1)
            rows.append({"year": year, "score_positive": s, "n": n})
        sign = 1 if (np.nanmean(deltas) if deltas else 0.0) >= 0 else -1
        year_scores = []
        for year in DISCOVERY_YEARS:
            p, q = match_pairs(x[x.year == year], med, iqr)
            s, n = paired_score(q, p, c, sign)
            year_scores.append(s)
        direction_rows.append({
            "candidate": c,
            "direction": sign,
            "discovery_mean_score": float(np.nanmean(year_scores)) if year_scores else float("nan"),
            "discovery_min_score": float(np.nanmin(year_scores)) if year_scores else float("nan"),
            "discovery_year_scores": rows,
            "n_discovery_pairs": int(np.nansum([r["n"] for r in rows])),
        })

    # Freeze candidate directions from discovery, then score 2023 and 2024 untouched.
    results = []
    for r in direction_rows:
        c = r["candidate"]
        sign = int(r["direction"])
        vq = x[x.year == VALIDATION_YEAR]
        vp, vq = match_pairs(vq, med, iqr)
        vs, vn = paired_score(vq, vp, c, sign)
        hq = x[x.year == HOLDOUT_YEAR]
        hp, hq = match_pairs(hq, med, iqr)
        hs, hn = paired_score(hq, hp, c, sign)
        hpv = permutation_p(hq, hp, c, sign)
        results.append({
            **r,
            "validation_2023_score": vs,
            "validation_2023_n": vn,
            "holdout_2024_score": hs,
            "holdout_2024_n": hn,
            "holdout_2024_perm_p": hpv,
        })

    results.sort(key=lambda r: (-(r["holdout_2024_score"] if np.isfinite(r["holdout_2024_score"]) else -1), -(r["discovery_min_score"] if np.isfinite(r["discovery_min_score"]) else -1)))

    payload = {
        "experiment": "TIAMAT_PATH_MEMORY_COURT_V4",
        "classification": "experimental/non-authoritative",
        "target": "future_3_to_4_within_6h",
        "present_state": BASE,
        "causal_rule": "every history feature uses only t-1 and earlier; no current-t inclusion",
        "matching": {
            "geometry_fit_years": list(DISCOVERY_YEARS),
            "metric": "Euclidean distance in robust IQR-standardized present state",
            "caliper": CALIPER,
            "minimum_temporal_separation_h": MIN_SEP_H,
            "one_to_one": True,
        },
        "selection_rule": "candidate direction frozen from 2020-2022; no candidate selected using 2023 or 2024",
        "results": results,
        "interpretation": "A path-memory candidate survives only if direction is stable in discovery, remains above 0.5 in 2023, and retains materially above-chance paired score in the untouched 2024 holdout. The 2024 permutation p-value is descriptive across the pre-registered candidate panel; it is not a license to select after seeing the holdout.",
    }
    Path(out).write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(json.dumps(payload, indent=2, allow_nan=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
