"""HYDRA H3 differential court V1.

Usage:
    python experiments/hydra_h3_differential_v1.py path/to/layer1_structured_hazard_arm_timeseries(15).csv

The native TIAMAT labels are retained only for post-hoc comparison. They are
never passed into HydraEvidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, roc_auc_score

from hydra import HydraEngine, HydraEvidence

REQUIRED = {
    "open_time", "SimpleShock", "LiveDeficit", "RecoveryWeakness_v1",
    "episode_age_h", "regime_30d", "episode_type", "hazard_raw",
    "hazard_score", "entry_path", "Crash72",
}


def num(row: pd.Series, name: str, default: float = 0.0) -> float:
    value = row[name]
    return default if pd.isna(value) else float(value)


def evidence(row: pd.Series, prev_ld: float | None) -> HydraEvidence:
    return HydraEvidence(
        hazard_raw=num(row, "hazard_raw"),
        hazard_score=num(row, "hazard_score"),
        live_deficit=num(row, "LiveDeficit"),
        simple_shock=num(row, "SimpleShock"),
        recovery_weakness=num(row, "RecoveryWeakness_v1"),
        episode_age_h=int(num(row, "episode_age_h")),
        prev_live_deficit=prev_ld,
        regime=str(row["regime_30d"]) if not pd.isna(row["regime_30d"]) else "unknown",
    )


def main(path: str) -> int:
    df = pd.read_csv(Path(path))
    missing = REQUIRED - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")
    if len(df) != 43848:
        raise SystemExit(f"Expected canonical 43,848 rows; got {len(df)}")

    # Native H3 starts are identified from the substrate only. Native labels
    # never enter Hydra's evidence vector.
    starts = (df["entry_path"].eq("3_to_4") & df["episode_age_h"].eq(1))
    if int(starts.sum()) != 169:
        raise SystemExit(f"Expected 169 native 3_to_4 starts; got {int(starts.sum())}")

    engine = HydraEngine()
    state = engine.replay(
        evidence(r, prev_ld)
        for r, prev_ld in zip(
            (row for _, row in df.iterrows()),
            [None] + df["LiveDeficit"].fillna(0.0).tolist()[:-1],
        )
    )
    decisions = state

    rows = []
    for i, d in enumerate(decisions):
        rows.append({
            "row": i,
            "open_time": df.iloc[i]["open_time"],
            "hydra_action": d.action,
            "hydra_active": d.state.active,
            "hazard": d.state.hazard,
            "burden": d.state.burden,
            "recovery": d.state.recovery,
            "trajectory": d.state.trajectory,
            "persistence": d.state.persistence,
            "lane_score": d.module_scores["lane"],
            # Post-hoc comparison fields only.
            "native_h3_start": bool(starts.iloc[i]),
            "native_episode_type": df.iloc[i]["episode_type"],
            "crash72": int(df.iloc[i]["Crash72"]),
        })
    out = pd.DataFrame(rows)
    h3 = out[out.native_h3_start].copy()

    print(f"rows={len(df)}")
    print(f"native_h3_starts={len(h3)}")
    print("hydra_actions_at_h3_starts=")
    print(h3.hydra_action.value_counts().to_string())
    print("native_episode_type_by_hydra_action=")
    print(pd.crosstab(h3.native_episode_type, h3.hydra_action).to_string())
    print(f"h3_start_activation_rate={h3.hydra_active.mean():.6f}")
    print(f"h3_start_crash72_rate={h3.crash72.mean():.6f}")

    for col in ("hazard", "burden", "trajectory", "lane_score"):
        if h3.crash72.nunique() == 2:
            print(f"auc_{col}_vs_crash72={roc_auc_score(h3.crash72, h3[col]):.6f}")

    # A deliberately transparent first-generation composite, for comparison
    # only; it is not promoted to a Hydra coordinator coefficient.
    composite = 0.40 * h3.hazard + 0.30 * h3.burden + 0.20 * h3.trajectory + 0.10 * (1.0 - h3.recovery)
    if h3.crash72.nunique() == 2:
        print(f"auc_composite_vs_crash72={roc_auc_score(h3.crash72, composite):.6f}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    raise SystemExit(main(parser.parse_args().csv))
