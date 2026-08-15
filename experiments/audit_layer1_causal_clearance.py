"""Audit the recovered Layer-1 panel before causal/Hydra use.

This is an integrity audit, not a causal proof. It keeps native Hazard and
hindsight annotations quarantined, independently diagnoses the Crash72 label
against a transparent 72-hour future-drawdown proxy, and checks structural
invariants. It deliberately refuses to promote the proxy target or Hazard
fields into the causal feature set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

EXPECTED_ROWS = 43848
EXPECTED_H3_STARTS = 169
EXPECTED_SOURCE_SHA256 = "6f0dc516fdf3313ab27a38d942504d073faccba4067877531b44c219c5e4b31a"
RUNTIME_CANDIDATES = [
    "open_time", "close", "SimpleShock", "LiveDeficit",
    "RecoveryWeakness_v1", "recovery_gate", "regime_30d",
]
HAZARD_QUARANTINE = ["hazard_raw", "hazard_score", "hazard_bucket"]
HINDSIGHT_QUARANTINE = [
    "Crash72", "entry_path", "episode_age_h", "duration_bucket", "episode_type",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def future_min_close(close: pd.Series, horizon: int = 72) -> pd.Series:
    return pd.concat([close.shift(-i) for i in range(1, horizon + 1)], axis=1).min(axis=1)


def audit(path: Path) -> dict:
    df = pd.read_csv(path)
    required = set(RUNTIME_CANDIDATES + HAZARD_QUARANTINE + HINDSIGHT_QUARANTINE)
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(df)}")

    source_sha = sha256(path)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "source SHA-256 mismatch: "
            f"expected {EXPECTED_SOURCE_SHA256}, got {source_sha}"
        )

    ts = pd.to_datetime(df["open_time"], errors="raise", utc=True)
    if not ts.is_monotonic_increasing:
        raise ValueError("open_time must be strictly chronological")
    duplicates = int(ts.duplicated().sum())
    if duplicates:
        raise ValueError(f"duplicate timestamps: {duplicates}")

    step_hours = ts.diff().dropna().dt.total_seconds() / 3600.0
    if not step_hours.eq(1.0).all():
        bad = step_hours[~step_hours.eq(1.0)]
        raise ValueError(f"non-hourly gaps detected; examples={bad.head(5).to_dict()}")

    starts = ((df["entry_path"] == "3_to_4") & (df["episode_age_h"] == 1))
    h3 = int(starts.sum())
    if h3 != EXPECTED_H3_STARTS:
        raise ValueError(f"expected {EXPECTED_H3_STARTS} H3 starts, got {h3}")

    close = pd.to_numeric(df["close"], errors="raise")
    if (close <= 0).any():
        raise ValueError("close must be strictly positive")
    fmin = future_min_close(close)
    fdd = fmin / close - 1.0
    y = pd.to_numeric(df["Crash72"], errors="raise").astype(int)
    if not y.isin([0, 1]).all():
        raise ValueError("Crash72 must be binary")
    proxy = (fdd <= -0.15).astype(int)
    usable = fdd.notna()

    return {
        "status": "AUDIT_ONLY_NOT_CAUSALLY_CLEARED",
        "source": str(path),
        "source_sha256": source_sha,
        "rows": int(len(df)),
        "hourly_cadence_verified": True,
        "timestamp_monotonic": True,
        "duplicate_timestamps": 0,
        "h3_start_count": h3,
        "runtime_candidates": RUNTIME_CANDIDATES,
        "hazard_quarantine": HAZARD_QUARANTINE,
        "hindsight_quarantine": HINDSIGHT_QUARANTINE,
        "target": "Crash72",
        "target_positive_count": int(y.sum()),
        "target_negative_count": int((1 - y).sum()),
        "diagnostic_proxy": {
            "definition": "min(close[t+1:t+72]) / close[t] - 1 <= -0.15",
            "usable_rows": int(usable.sum()),
            "agreement_with_supplied_target": float((proxy[usable] == y[usable]).mean()),
            "false_positives_vs_supplied": int(((proxy == 1) & (y == 0) & usable).sum()),
            "false_negatives_vs_supplied": int(((proxy == 0) & (y == 1) & usable).sum()),
            "is_not_promoted_to_target": True,
        },
        "feature_clearance": {
            "runtime_lineage_verified": False,
            "hazard_cleared": False,
            "target_constructor_recovered": False,
            "promotion_allowed": False,
        },
        "next_required_evidence": [
            "recover exact Crash72 constructor",
            "recover canonical upstream LiveDeficit/robust24h_downside lineage",
            "verify SimpleShock rolling windows are trailing",
            "verify RecoveryWeakness update timing and inputs",
            "verify recovery_gate and regime_30d are runtime-observable",
            "run Hazard-only independent 2024 consequence test",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()
    result = audit(args.csv)
    text = json.dumps(result, indent=2) + "\n"
    print(text, end="")
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
