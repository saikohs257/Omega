"""Minimal stress probe for the state-vs-damage divergence."""

from tiamat.engine import TiamatEngine

CASES = [
    ("baseline", {"B": 0.0, "V": 1.0, "D": 0.0}),
    ("state_only_poke", {"B": 0.0, "V": 1.0, "D": 1e-9}),
    ("damage_poke", {"B": 0.0, "V": 1.0, "D": 1e-6}),
]

for name, values in CASES:
    engine = TiamatEngine()
    result = engine.diagnose(**values)
    print({"case": name, **values, "diagnose": result})
