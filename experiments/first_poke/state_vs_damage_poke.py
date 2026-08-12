"""Minimal stress probe for the TIAMAT D decision boundary.

The probe keeps evidence constant and varies only initial state damage D.
It first repeats the three microscopic matched pokes, then sweeps D across
orders of magnitude to find the first observable/guard change. This is an
experiment only; it does not alter the canonical TIAMAT runtime.
"""
from __future__ import annotations

import os

from tiamat.engine import TiamatEngine
from tiamat.state import TiamatState

EVIDENCE = {"B": 0.0, "V": 1.0}
CASES = [("baseline", 0.0), ("state_only_poke", 1e-9), ("damage_poke", 1e-6)]
SWEEP = [0.0, 1e-12, 1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4,
         1e-3, 1e-2, 5e-2, 1e-1, 2.5e-1, 5e-1, 7.5e-1, 9e-1, 1.0]


def run_case(engine: TiamatEngine, damage: float) -> dict:
    state = TiamatState(B=0.0, V=1.0, D=damage)
    result = engine.diagnose(state, EVIDENCE)
    return {
        "input_D": damage,
        "resulting_D": result["state"]["D"],
        "mode": result["state"]["mode"],
        "hazard_raw": result["observables"]["hazard_raw"],
        "hazard_score": result["observables"]["hazard_score"],
        "guards": tuple(g["name"] for g in result["guards"] if g["triggered"]),
    }


print({"experiment": "state_vs_damage_boundary_poke",
       "github_sha": os.environ.get("GITHUB_SHA", "unknown"),
       "evidence": EVIDENCE})
engine = TiamatEngine()
print({"matched_cases": [{"case": name, **run_case(engine, damage)} for name, damage in CASES]})

previous = run_case(engine, SWEEP[0])
first_change = None
for damage in SWEEP[1:]:
    current = run_case(engine, damage)
    if (current["mode"] != previous["mode"] or current["guards"] != previous["guards"]) and first_change is None:
        first_change = {"previous": previous, "current": current}
    previous = current
    print({"sweep": current})
print({"first_discrete_change": first_change})
