"""Minimal stress probe for state-vs-damage divergence.

The probe uses the canonical TIAMAT API. It changes only the initial D value
between matched cases and keeps the evidence constant. D is intentionally not
present in the evidence because transition() treats evidence D as the observed
next-state D and would otherwise overwrite the state-only poke.
"""
from __future__ import annotations

import os

from tiamat.engine import TiamatEngine
from tiamat.state import TiamatState

EVIDENCE = {
    "B": 0.0,
    "V": 1.0,
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
