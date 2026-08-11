"""Exhaustive DVQT relationship probe.

The harness is deliberately descriptive: it enumerates pairwise, signed,
lagged, attenuated, phase-conditioned and higher-order probes.  It does not
claim causality.  Its job is to expose which transformations destroy or
preserve predictive information and therefore identify candidate relationships
for reverse engineering.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

FEATURES = ("D", "V", "B", "tau", "mode", "phase", "history")
LAGS = (-3, -2, -1, 0, 1, 2, 3)
AMPLITUDES = (0.25, 0.5, 1.0, 2.0, 4.0)
SIGNS = (1.0, -1.0)


@dataclass(frozen=True)
class Probe:
    kind: str
    left: str
    right: str | None = None
    lag: int = 0
    amplitude: float = 1.0
    sign: float = 1.0
    condition: str | None = None


def probes(features: Sequence[str] = FEATURES) -> list[Probe]:
    out: list[Probe] = []
    for left, right in combinations(features, 2):
        out.append(Probe("pair", left, right))
        for lag in LAGS:
            out.append(Probe("lag", left, right, lag=lag))
        for amp in AMPLITUDES:
            out.append(Probe("amplitude", left, right, amplitude=amp))
        for sign in SIGNS:
            out.append(Probe("sign", left, right, sign=sign))
        for condition in ("early", "mid", "late", "high_phase", "low_phase"):
            out.append(Probe("phase_condition", left, right, condition=condition))
        out.append(Probe("direction", left, right, lag=1))
        out.append(Probe("direction", right, left, lag=1))
    for a, b, c in __import__("itertools").combinations(features, 3):
        out.append(Probe("triple", f"{a}+{b}", c))
    return out


def relationship_score(single_best: float, joint: float) -> float:
    """Positive means joint information exceeds the best singleton."""
    return joint - single_best


if __name__ == "__main__":
    ps = probes()
    print(f"features={FEATURES}")
    print(f"probes={len(ps)}")
    print("probe_families=pair,lag,amplitude,sign,phase_condition,direction,triple")
