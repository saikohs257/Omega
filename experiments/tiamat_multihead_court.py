"""Historical TIAMAT multi-head court.

This is a research-only harness. It keeps each TIAMAT head scoped to its
native topology/timing seat and never constructs a global TIAMAT score.

Expected input columns are documented in the historical HF9 handoff.  The
runner fails closed when a required field is absent rather than silently
substituting a different representation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

PATHS = ("0_to_4", "2_to_4", "3_to_4", "4_to_4")


def _auc(y: pd.Series, score: pd.Series) -> float:
    mask = y.notna() & score.notna()
    if mask.sum() < 2 or y.loc[mask].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(y.loc[mask].astype(int), score.loc[mask]))


def _brier(y: pd.Series, score: pd.Series) -> float:
    mask = y.notna() & score.notna()
    if mask.sum() == 0:
        return float("nan")
    s = score.loc[mask].astype(float)
    lo, hi = float(s.min()), float(s.max())
    if hi <= lo:
        p = np.full(len(s), 0.5)
    else:
        p = (s.to_numpy() - lo) / (hi - lo)
    return float(brier_score_loss(y.loc[mask].astype(int), p))


def score_heads(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "topology_path",
        "LiveDeficit",
        "hazard_raw",
        "SimpleShock",
        "next_15h_4_survival",
        "next_15h_4_any",
        "next_trigger_6h",
        "next_trigger_24h",
        "next_trigger_48h",
        "ExitBridgeDeficit",
        "PriorCarryDeficit",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError("Missing required historical-court columns: " + ", ".join(missing))

    rows: list[dict[str, object]] = []
    head_specs = {
        "0_to_4": ("false_calm_ignition", lambda x: x["SimpleShock"] + 0.05 * x["hazard_raw"]),
        "2_to_4": ("reset_drag_release", lambda x: x["LiveDeficit"]),
        "3_to_4": (
            "recovery_inversion",
            lambda x: x["LiveDeficit"] + 0.05 * x["hazard_raw"] - x["shock_0_4h_max"],
        ),
        "4_to_4": (
            "ceiling_trap",
            lambda x: x["LiveDeficit"] + 0.20 * x["hazard_raw"] + 0.10 * x["SimpleShock"],
        ),
    }

    for path, (head_name, formula) in head_specs.items():
        scoped = df[df["topology_path"] == path].copy()
        if scoped.empty:
            continue
        scoped["score"] = formula(scoped)
        y_survive = scoped["next_15h_4_survival"]
        y_any = scoped["next_15h_4_any"]
        rows.append({
            "head": head_name,
            "native_scope": path,
            "n": int(len(scoped)),
            "auc_next15_survival": _auc(y_survive, scoped["score"]),
            "brier_next15_survival": _brier(y_survive, scoped["score"]),
            "auc_next15_any": _auc(y_any, scoped["score"]),
            "brier_next15_any": _brier(y_any, scoped["score"]),
            "timing_legality": "SCOPED_NATIVE_PATH",
            "verdict": "DIAGNOSTIC",
            "allowed_use": path,
            "forbidden_use": "global resolver / universal scalar",
        })

    for name, target in (
        ("ExitBridge", "next_trigger_6h"),
        ("ExitBridge", "next_trigger_24h"),
        ("ExitBridge", "next_trigger_48h"),
        ("PriorCarry", "next_trigger_6h"),
        ("PriorCarry", "next_trigger_24h"),
        ("PriorCarry", "next_trigger_48h"),
    ):
        score_col = "ExitBridgeDeficit" if name == "ExitBridge" else "PriorCarryDeficit"
        rows.append({
            "head": name,
            "native_scope": "episode_boundary" if name == "ExitBridge" else "episode_shift",
            "n": int(df[target].notna().sum()),
            "target": target,
            "auc": _auc(df[target], df[score_col]),
            "brier": _brier(df[target], df[score_col]),
            "timing_legality": "ENDPOINT_EXACT" if name == "ExitBridge" else "SHIFTED_PRIOR",
            "verdict": "DIAGNOSTIC",
            "allowed_use": target,
            "forbidden_use": "current-row substitution / global resolver",
        })

    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("tiamat_multihead_court.csv"))
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    result = score_heads(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
