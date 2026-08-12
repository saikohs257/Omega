"""Minimal stress probe for state-vs-damage divergence.

The probe uses the canonical TIAMAT API. It changes only the initial D value
between matched cases and keeps the evidence constant, so any output change
is attributable to D rather than to a different calling path.
"""
from __future__ import annotations

import os

from tiamat.engine import TiamatEngine
from tiamat.state import TiamatState

EVIDENCE = {
    "B": 0.0,
    "V": 1.0,
    "D": 0.0,
}

CASES = [
    ("baseline", 0.0),
    ("state_only_poke", 1e-9),
    ("damage_poke", 1e-6),
]

print({
    "experiment": "state_vs_damage_poke",
    "github_sha": os.environ.get("GITHUB_SHA", "unknown"),
})

engine = TiamatEngine()
for name, damage in CASES:
    state = TiamatState(B=0.0, V=1.0, D=damage)
    result = engine.diagnose(state, EVIDENCE)
    print({
        "case": name,
        "input_state": state.to_dict(),
        "evidence": EVIDENCE,
        "diagnose": result,
    })
