"""DVQT inertia probes.

Treat each observable as a state with persistence.  The lab defines controlled
perturbations to estimate how much each variable resists change, how long its
effect persists, and whether that persistence is intrinsic or induced by other
variables.  This is an experimental design layer; it does not assert physical
inertia.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

VARIABLES = ("D", "V", "B", "tau", "mode", "phase", "history")
SHOCKS = ("step", "pulse", "sign_flip", "zero", "randomize", "hold")
DELAYS = tuple(range(0, 11))
AMPLITUDES = (0.1, 0.25, 0.5, 1.0, 2.0, 4.0)

@dataclass(frozen=True)
class InertiaProbe:
    variable: str
    shock: str
    delay: int = 0
    amplitude: float = 1.0
    context: str = "baseline"


def probes() -> list[InertiaProbe]:
    out = [InertiaProbe(v, s, d, a)
           for v in VARIABLES
           for s in SHOCKS
           for d in DELAYS
           for a in AMPLITUDES]
    for a, b in combinations(VARIABLES, 2):
        for s in ("shock_a", "shock_b", "shock_both", "release_a", "release_b"):
            out.append(InertiaProbe(a, s, context=b))
    return out


def persistence_weight(values: list[float]) -> float:
    """Area-under-persistence proxy; lower decay means greater inertia."""
    if not values:
        return 0.0
    return sum(max(0.0, abs(v)) for v in values)

if __name__ == "__main__":
    ps = probes()
    print(f"inertia_probes={len(ps)}")
    print(f"variables={VARIABLES}")
    print(f"shocks={SHOCKS}")
    print(f"delays={DELAYS}")
    print(f"amplitudes={AMPLITUDES}")
