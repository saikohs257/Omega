from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HORIZON_H = 6
MIN_SEPARATION_H = 168
HOLDOUT_YEAR = 2024


def future_3_to_4(d: pd.DataFrame) -> pd.Series:
    x = d[["open_time", "entry_path"]].sort_values("open_time").reset_index()
    t = x["open_time"].to_numpy(dtype="datetime64[ns]")
    labels = np.zeros(len(x), dtype=np.int8)
    paths = x["entry_path"].astype(str).to_numpy()
    for i in range(len(x)):
        upper = t[i] + np.timedelta64(HORIZON_H, "h")
        j = np.searchsorted(t, upper, side="right")
        if j > i + 1:
            labels[i] = np.any(paths[i + 1:j] == "3_to_4")
    return pd.Series(labels, index=x["index"].to_numpy()).reindex(d.index).fillna(0).astype(int)


def main(csv: Path, out: Path) -> None:
    d = pd.read_csv(csv)
    for c in ["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["open_time"] = pd.to_datetime(d["open_time"], utc=True)
    d["target"] = future_3_to_4(d)
    te = d[d.open_time.dt.year == HOLDOUT_YEAR].copy().reset_index(drop=True)
    q = te.dropna(subset=["SimpleShock", "LiveDeficit", "RecoveryWeakness_v1", "hazard_raw", "target"]).copy().reset_index(drop=True)

    pos = q[q.target.eq(1)].copy()
    neg = q[q.target.eq(0)].copy()
    if pos.empty or neg.empty:
        raise RuntimeError(f"Need both classes: pos={len(pos)} neg={len(neg)}")

    p = pos.open_time.to_numpy(dtype="datetime64[ns]")
    n = neg.open_time.to_numpy(dtype="datetime64[ns]")
    all_min = np.inf
    for tp in p:
        gap_h = np.abs((n - tp) / np.timedelta64(1, "h"))
        all_min = min(all_min, float(gap_h.min()))

    eligible_pairs = 0
    for tp in p:
        gap_h = np.abs((n - tp) / np.timedelta64(1, "h"))
        eligible_pairs += int(np.sum(gap_h >= MIN_SEPARATION_H))

    payload = {
        "experiment": "TIAMAT_PATH_MEMORY_TIMESTAMP_DIAGNOSTIC_V1",
        "holdout_year": HOLDOUT_YEAR,
        "target": f"future_3_to_4_within_{HORIZON_H}h",
        "positive_rows": int(len(pos)),
        "negative_rows": int(len(neg)),
        "holdout_min_time": str(q.open_time.min()),
        "holdout_max_time": str(q.open_time.max()),
        "positive_min_time": str(pos.open_time.min()),
        "positive_max_time": str(pos.open_time.max()),
        "negative_min_time": str(neg.open_time.min()),
        "negative_max_time": str(neg.open_time.max()),
        "minimum_opposite_outcome_separation_h": float(all_min),
        "eligible_opposite_pairs_after_168h": int(eligible_pairs),
        "timestamp_method": "datetime64[ns] timedelta division; no integer-unit assumption",
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(out.read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
