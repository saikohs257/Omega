"""Scoped head interrogation matrix.

This is an experiment, not a canonical head implementation. It uses the
original TiamatState/transition/guard surface directly and asks whether each
claimed head scope has a distinct observable transition seat. No DVB/DVQT
projection is used.
"""
from __future__ import annotations

import json
import os
from itertools import product

from tiamat.engine import TiamatEngine
from tiamat.modes import TiamatMode
from tiamat.state import TiamatState

SCOPES = {
    "H0": (TiamatMode.QUIESCENT, TiamatMode.RELAXATION),
    "H2": (TiamatMode.EXCITATION, TiamatMode.RELAXATION),
    "H3": (TiamatMode.COUPLED_TRANSFER, TiamatMode.RELAXATION),
    "H4": (TiamatMode.HAZARD, TiamatMode.HAZARD),
    "ExitBridge": (TiamatMode.RELAXATION, TiamatMode.REFRACTORY),
}

BASE = dict(B=0.20, V=0.10, D=0.15, tau_D=4.0, tau_mode=3.0)


def state(mode: TiamatMode, **changes: object) -> TiamatState:
    values = dict(BASE, mode=mode)
    values.update(changes)
    return TiamatState(**values)


def observe(engine: TiamatEngine, mode: TiamatMode, **evidence: object) -> dict:
    s = state(mode, **{k: v for k, v in evidence.items() if k in {"B", "V", "D", "tau_D", "tau_mode"}})
    result = engine.diagnose(s, evidence)
    return {
        "from": mode.value,
        "to": result["state"]["mode"],
        "guards": [g["name"] for g in result["guards"] if g["triggered"]],
        "hazard_raw": result["observables"]["hazard_raw"],
    }


def main() -> None:
    engine = TiamatEngine()
    out = {"experiment": "head_scope_interrogation", "github_sha": os.environ.get("GITHUB_SHA", "unknown"), "results": {}}

    # Direct transition-seat probes. Thresholds are chosen only to expose the
    # existing guard/transition branches; they are not proposed head formulas.
    probes = {
        "H0": [("V_positive", {"V": 0.5}), ("V_zero", {"V": 0.0})],
        "H2": [("coupled", {"coupled_transfer": True}), ("relax", {"V": -0.5})],
        "H3": [("promotion", {"promotion_threshold": 2, "promotion_count": 2}), ("relax", {"V": -0.5})],
        "H4": [("damage_guard", {"damage_threshold": 0.1}), ("relax", {"V": -0.5})],
        "ExitBridge": [("refractory", {"enter_refractory": True}), ("release", {"refractory_release": True})],
    }

    for head, cases in probes.items():
        src, dst = SCOPES[head]
        rows = []
        for name, evidence in cases:
            rows.append({"case": name, "expected_scope": [src.value, dst.value], "observation": observe(engine, src, **evidence)})
        out["results"][head] = rows

    # Cross-scope matrix: same perturbations applied to every source mode.
    perturbations = {
        "positive_V": {"V": 0.5},
        "negative_V": {"V": -0.5},
        "coupled": {"coupled_transfer": True},
        "promotion": {"promotion_threshold": 2, "promotion_count": 2},
        "damage": {"damage_threshold": 0.1},
        "refractory": {"enter_refractory": True},
    }
    matrix = []
    for mode, (label, evidence) in product(TiamatMode, perturbations.items()):
        matrix.append({"mode": mode.value, "perturbation": label, "observation": observe(engine, mode, **evidence)})
    out["cross_scope_matrix"] = matrix

    print(json.dumps(out, default=str))


if __name__ == "__main__":
    main()
