"""Anti-leakage court for recovery-minus-burden derived from canonical primitives.

The canonical spine remains immutable: rr_recovery_minus_burden is reconstructed
locally from RecoveryWeakness_v1 - LiveDeficit, with both lagged one hour.
Evaluation uses non-overlapping 72h anchors across every phase offset, with
2024 held out. The anchor operation preserves a real source row rather than
using DataFrameGroupBy.first(), which can synthesize a row column-by-column.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from hydra_relative_recovery_court_v1 import history

TARGET = "Crash72"
FEATURE = "rr_recovery_minus_burden"
PERIOD = 72


def score(tr: pd.DataFrame, te: pd.DataFrame, col: str):
    tr = tr.dropna(subset=[col, TARGET])
    te = te.dropna(subset=[col, TARGET])
    classes = set(pd.to_numeric(tr[TARGET], errors="coerce").dropna().astype(int).unique())
    teclasses = set(pd.to_numeric(te[TARGET], errors="coerce").dropna().astype(int).unique())
    if classes != {0, 1} or not teclasses.issubset({0, 1}) or len(teclasses) < 2:
        return None
    x0 = tr.loc[tr[TARGET] == 0, col].astype(float)
    x1 = tr.loc[tr[TARGET] == 1, col].astype(float)
    if len(x0) < 20 or len(x1) < 5:
        return None
    vals = te[col].astype(float).to_numpy()
    ref1 = x1.to_numpy()
    ref0 = x0.to_numpy()
    p = np.array([(np.mean(ref1 <= v) + np.mean(ref0 <= v)) / 2 for v in vals])
    return float(roc_auc_score(te[TARGET].astype(int), p))


def nonoverlap(d: pd.DataFrame, offset: int) -> pd.DataFrame:
    x = d.sort_values("open_time").reset_index(drop=True).copy()
    h = pd.to_datetime(x.open_time, utc=True).astype("int64") // 10**9 // 3600
    x["_anchor"] = ((h - offset) // PERIOD) * PERIOD + offset
    return x.drop_duplicates("_anchor", keep="first").reset_index(drop=True)


def main(csv: Path, out: Path):
    raw = pd.read_csv(csv)
    d = history(raw)
    assert len(raw) == 43848
    starts = int(((d.entry_path == "3_to_4") & (d.episode_age_h == 1)).sum())
    assert starts == 169

    # Derived compatibility coordinate: never written back to canonical storage.
    d[FEATURE] = d["RecoveryWeakness_v1"].shift(1) - d["LiveDeficit"].shift(1)
    d["rr_lag24"] = d[FEATURE].shift(24)
    d["rr_lag168"] = d[FEATURE].shift(168)
    d["rr_lead24"] = d[FEATURE].shift(-24)  # deliberately invalid negative control
    d["rr_innov24"] = d[FEATURE] - d[FEATURE].shift(24)
    d["year"] = d.open_time.dt.year

    controls = [FEATURE, "rr_lag24", "rr_lag168", "rr_lead24", "rr_innov24"]
    rows = []
    for off in range(PERIOD):
        x = nonoverlap(d, off)
        tr = x[x.year < 2024]
        te = x[x.year == 2024]
        for c in controls:
            a = score(tr, te, c)
            if a is not None:
                rows.append({
                    "offset": off,
                    "feature": c,
                    "auc": a,
                    "n_train": len(tr),
                    "n_test": len(te),
                    "train_classes": sorted(set(tr[TARGET].astype(int))),
                    "test_classes": sorted(set(te[TARGET].astype(int))),
                })

    frame = pd.DataFrame(rows)
    summary = []
    for c in controls:
        q = frame.loc[frame.feature == c, "auc"].dropna()
        summary.append({
            "feature": c,
            "valid_offsets": int(len(q)),
            "median_auc": float(q.median()) if len(q) else None,
            "q25": float(q.quantile(.25)) if len(q) else None,
            "q75": float(q.quantile(.75)) if len(q) else None,
            "min": float(q.min()) if len(q) else None,
            "max": float(q.max()) if len(q) else None,
        })

    payload = {
        "experiment": "hydra_relative_recovery_falsification_court_v2",
        "protocol": "2024 frozen holdout; 72 non-overlap phase offsets; binary-target guard; derived feature reconstructed from canonical primitives; source-row-preserving anchors",
        "canonical_rows": len(raw),
        "canonical_h3_starts": starts,
        "summary": summary,
        "offsets": rows,
        "interpretation_rule": "real-time memory is stronger evidence only if its distribution materially exceeds lag, lead, and innovation controls across offsets; invalid offsets are reported, never coerced to multiclass",
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(json.dumps(payload, indent=2, allow_nan=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    main(args.csv, args.out)
