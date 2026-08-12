"""Direct interrogation of TIAMAT's original M3 state variables.

This is deliberately NOT a DVB/DVQT projection.  It perturbs the original
TiamatState fields directly and records the actual next-mode/guard surface.
No canonical runtime code is changed by this experiment.
"""
from __future__ import annotations

import json
import os
from itertools import combinations

from tiamat.engine import TiamatEngine
from tiamat.modes import TiamatMode
from tiamat.state import TiamatState

BASE = dict(B=0.20, V=0.10, D=0.15, tau_D=4.0, tau_mode=3.0, mode=TiamatMode.QUIESCENT)
FIELDS = ("B", "V", "D", "tau_D", "tau_mode")


def observe(engine: TiamatEngine, state: TiamatState) -> dict:
    result = engine.diagnose(state, {})
    return {
        "input": state.to_dict(),
        "mode": result["state"]["mode"],
        "guards": tuple(g["name"] for g in result["guards"] if g["triggered"]),
        "hazard_raw": result["observables"]["hazard_raw"],
        "hazard_score": result["observables"]["hazard_score"],
        "residual_load": result["observables"]["residual_load"],
        "recovery": result["observables"]["recovery"],
        "pressure": result["observables"]["pressure"],
        "momentum": result["observables"]["momentum"],
    }


def make(**changes: object) -> TiamatState:
    values = dict(BASE)
    values.update(changes)
    return TiamatState(**values)


def main() -> None:
    engine = TiamatEngine()
    print(json.dumps({"experiment": "original_tiamat_state_interrogation", "github_sha": os.environ.get("GITHUB_SHA", "unknown"), "base": BASE}, default=str))

    baseline = observe(engine, make())
    print(json.dumps({"baseline": baseline}, default=str))

    # One-at-a-time perturbations use original state variables, not DVB aliases.
    grids = {
        "B": (0.0, 0.1, 0.2, 0.4, 0.7, 1.0),
        "V": (-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0),
        "D": (0.0, 0.01, 0.05, 0.15, 0.25, 0.5, 0.9, 1.0),
        "tau_D": (0.0, 1.0, 3.0, 4.0, 8.0, 24.0),
        "tau_mode": (0.0, 1.0, 3.0, 8.0, 24.0),
    }
    for field in FIELDS:
        for value in grids[field]:
            result = observe(engine, make(**{field: value}))
            print(json.dumps({"one_at_a_time": field, "value": value, "result": result}, default=str))

    # Pairwise interventions: look specifically for non-additive changes in
    # discrete outcome or hazard relative to the two one-variable effects.
    for left, right in combinations(FIELDS, 2):
        left_value = grids[left][len(grids[left]) // 2]
        right_value = grids[right][len(grids[right]) // 2]
        result = observe(engine, make(**{left: left_value, right: right_value}))
        print(json.dumps({"pair": [left, right], "values": [left_value, right_value], "result": result}, default=str))


if __name__ == "__main__":
    main()
