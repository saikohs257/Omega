"""Anti-leakage court V3 for recovery-minus-burden.

The canonical spine contains the frozen Crash72 target but does not contain
experimental derived RR columns. Reconstruct RR through the exact shared
history() implementation used by the relative-recovery court, then run the
falsification tests on that reconstructed feature. No derived feature is
written back to the canonical spine.
"""
from __future__ import annotations
import argparse, json
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
    ytr = pd.to_numeric(tr[TARGET], errors="coerce").astype(int)
    yte = pd.to_numeric(te[TARGET], errors="coerce").astype(int)
    if set(ytr.unique()) != {0, 1} or set(yte.unique()) != {0, 1}:
        return None
    x0 = tr.loc[ytr == 0, col].astype(float).to_numpy()
    x1 = tr.loc[ytr == 1, col].astype(float).to_numpy()
    if len(x0) < 20 or len(x1) < 5:
        return None
    vals = te[col].astype(float).to_numpy()
    p = np.array([(np.mean(x1 <= v) + np.mean(x0 <= v)) / 2.0 for v in vals])
    return float(roc_auc_score(yte, p))


def nonoverlap(d: pd.DataFrame, offset: int) -> pd.DataFrame:
    x = d.sort_values("open_time").reset_index(drop=True).copy()
    h = pd.to_datetime(x.open_time, utc=True).astype("int64") // 10**9 // 3600
    anchor = ((h - offset) // PERIOD) * PERIOD + offset
    x["_anchor"] = anchor
    return x.groupby("_anchor", as_index=False).first()


def main(csv: Path, out: Path):
    raw = pd.read_csv(csv)
    assert len(raw) == 43848
    if TARGET not in raw:
        raise KeyError(f"missing {TARGET}")

    # Shared deterministic reconstruction. This is the same function used by
    # the upstream RR court and is strictly pre-event for the derived feature.
    d = history(raw)
    if FEATURE not in d:
        raise KeyError(f"history() did not reconstruct {FEATURE}")

    d.open_time = pd.to_datetime(d.open_time, utc=True)
    d[TARGET] = pd.to_numeric(d[TARGET], errors="coerce")
    bad = set(d[TARGET].dropna().astype(int).unique()) - {0, 1}
    if bad:
        raise ValueError(f"non-binary {TARGET} classes: {sorted(bad)}")

    # Provenance guard: RR must equal the exact shared formula.
    expected = (
        pd.to_numeric(d["RecoveryWeakness_v1"], errors="coerce").shift(1)
        - pd.to_numeric(d["LiveDeficit"], errors="coerce").shift(1)
    )
    if not np.allclose(d[FEATURE].to_numpy(float), expected.to_numpy(float), equal_nan=True):
        raise AssertionError("RR reconstruction does not match shared history() formula")

    d["year"] = d.open_time.dt.year
    controls = [
        FEATURE,
        "rr_lag24",
        "rr_lag168",
        "rr_lead24",
        "rr_innov24",
    ]
    d["rr_lag24"] = d[FEATURE].shift(24)
    d["rr_lag168"] = d[FEATURE].shift(168)
    d["rr_lead24"] = d[FEATURE].shift(-24)
    d["rr_innov24"] = d[FEATURE] - d[FEATURE].shift(24)

    rows = []
    for off in range(PERIOD):
        x = nonoverlap(d, off)
        tr = x[x.year < 2024]
        te = x[x.year == 2024]
        for c in controls:
            a = score(tr, te, c)
            if a is not None:
                rows.append({
                    "offset": off, "feature": c, "auc": a,
                    "n_train": len(tr), "n_test": len(te),
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
        "experiment": "hydra_relative_recovery_falsification_court_v3",
        "protocol": "2024 frozen holdout; 72 non-overlap phase offsets; shared history() RR reconstruction; binary-target guard; no candidate selection",
        "canonical_rows": len(raw),
        "feature": FEATURE,
        "target_source": "canonical Crash72",
        "feature_source": "shared hydra_relative_recovery_court_v1.history()",
        "summary": summary,
        "offsets": rows,
        "interpretation_rule": "real-time memory is stronger evidence only if its distribution materially exceeds lag, lead, and innovation controls across offsets; invalid offsets are reported, never coerced",
    }
    out.write_text(json.dumps(payload, indent=2, allow_nan=True))
    print(json.dumps(payload, indent=2, allow_nan=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    main(a.csv, a.out)
