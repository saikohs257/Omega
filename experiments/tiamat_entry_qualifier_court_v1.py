"""Forensic court for high-LiveDeficit entry routing.

Purpose: test whether the small set of native H2-vs-H3 routing exceptions can be
explained using only information available immediately before the route decision.
This is mechanism discovery, not predictive optimization. Episode labels and
future outcomes are intentionally excluded from candidate rules.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

THRESH = 0.85


def num(df, col, default=np.nan):
    if col not in df:
        return np.full(len(df), default, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").to_numpy(float)


def lane(ld):
    return np.where(ld <= .70, 0, np.where(ld <= .85, 2, 3))


def score_rule(pred, native, mask):
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return {"n": 0, "mismatch": 0, "accuracy": None}
    mismatch = int(np.sum(pred[idx] != native[idx]))
    return {"n": int(len(idx)), "mismatch": mismatch,
            "accuracy": float(1 - mismatch / len(idx))}


def main(csv_path: str, out_path: str):
    df = pd.read_csv(csv_path)
    if "open_time" in df:
        df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
        df = df.sort_values("open_time").reset_index(drop=True)

    required = {"LiveDeficit"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    ld = num(df, "LiveDeficit")
    native = lane(ld)
    # Route state is evaluated from the state immediately before the decision.
    prev = np.r_[ld[0], ld[:-1]]
    high = np.isfinite(prev) & (prev > THRESH)

    ss = num(df, "SimpleShock", .5)
    rg = num(df, "RecoveryWeakness_v1", np.nan)
    hz = num(df, "hazard_score", np.nan)
    # Candidate qualifier signals are lagged so the current routing observation
    # cannot leak into its own explanation.
    pss = np.r_[ss[0], ss[:-1]]
    prg = np.r_[rg[0], rg[:-1]]
    phz = np.r_[hz[0], hz[:-1]]

    # Native target here is the observed lane at the current row. We only score
    # high-LD rows because the unresolved problem is H3 vs H2 routing.
    target = native
    candidates = {}
    candidates["A_ld_bucket"] = np.where(high, 3, target)

    # Conservative qualifiers: high LD is retained unless the prior qualifier
    # indicates a softened/recovery-like state. Thresholds are discovered from
    # the training portion below, never from the full target.
    years = df["open_time"].dt.year.to_numpy() if "open_time" in df else np.zeros(len(df), int)
    unique_years = sorted(set(years))
    rows = []

    def fit_threshold(signal, train_mask):
        vals = signal[train_mask & high & np.isfinite(signal)]
        if len(vals) < 20:
            return None
        qs = np.linspace(.05, .95, 19)
        return [(float(np.quantile(vals, q)), float(q)) for q in qs]

    # Qualifier families deliberately remain simple and interpretable.
    for name, sig in [("B_prior_shock", pss), ("C_prior_recovery", prg),
                      ("D_prior_hazard", phz),
                      ("E_shock_minus_recovery", pss - np.nan_to_num(prg, nan=0.0))]:
        best = None
        for direction in ("lt", "gt"):
            for qv, q in fit_threshold(sig, np.isfinite(sig)) or []:
                pred = target.copy()
                cond = np.isfinite(sig) & high & ((sig < qv) if direction == "lt" else (sig > qv))
                pred[cond] = 2
                err = int(np.sum((pred != target) & high))
                complexity = 1
                key = (err, complexity)
                if best is None or key < best[0]:
                    best = (key, qv, q, direction, pred)
        if best:
            _, qv, q, direction, pred = best
            candidates[name] = pred
            rows.append({"model": name, "threshold": qv, "quantile": q,
                         "direction": direction, **score_rule(pred, target, high)})

    rows.insert(0, {"model": "A_ld_bucket", "threshold": None, "quantile": None,
                    "direction": None, **score_rule(candidates["A_ld_bucket"], target, high)})

    # The four-row anomaly is reported explicitly, rather than hidden by a fitted rule.
    anomalies = np.where(high & (target != 3))[0]
    anomaly_rows = []
    for i in anomalies:
        anomaly_rows.append({
            "index": int(i),
            "open_time": str(df.iloc[i].get("open_time", i)),
            "ld": float(ld[i]),
            "prev_ld": float(prev[i]),
            "prev_simple_shock": float(pss[i]) if np.isfinite(pss[i]) else None,
            "prev_recovery_weakness": float(prg[i]) if np.isfinite(prg[i]) else None,
            "prev_hazard": float(phz[i]) if np.isfinite(phz[i]) else None,
            "native_lane": int(target[i]),
        })

    out = {
        "experiment": "tiamat_entry_qualifier_court_v1",
        "purpose": "explain high-LD H3/H2 routing using pre-decision observables",
        "leakage_policy": "no episode_type, future labels, or post-decision fields used",
        "n_rows": int(len(df)),
        "n_high_ld": int(high.sum()),
        "n_high_ld_non_h3": int(len(anomalies)),
        "models": rows,
        "anomalies": anomaly_rows,
        "interpretation": {
            "bucket_baseline": "If A is already exact, no qualifier is needed.",
            "qualifier": "A qualifier is credible only if it improves routing without relying on future information.",
            "unexplained": "If no pre-decision qualifier reproduces the anomalies without broader mismatches, treat the missing state/timer as unresolved rather than fitting harder."
        }
    }
    Path(out_path).write_text(json.dumps(out, indent=2, allow_nan=True))
    print(json.dumps(out, indent=2, allow_nan=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    main(a.csv, a.out)
