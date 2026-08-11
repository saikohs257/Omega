"""B fingerprint and substitute-representation probe plan.

This module defines the candidate transformations to test against B without
claiming any one is equivalent. The runner can use these definitions to compare
B with algebraic, temporal, phase, and interaction-derived substitutes.
"""
from __future__ import annotations

from dataclasses import dataclass

B_LAGS = tuple(range(-10, 11))
B_AMPS = (0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
B_SIGNS = (1.0, -1.0)

SUBSTITUTES = (
    "D*V",
    "abs(D-V)",
    "D/V",
    "D+V",
    "D-V",
    "sign(D)*sign(V)",
    "dD*V",
    "D*dV",
    "rolling(D*V)",
    "lagged(D*V)",
    "phase_conditioned(D*V)",
)

@dataclass(frozen=True)
class BProbe:
    kind: str
    transform: str
    lag: int = 0
    amplitude: float = 1.0
    sign: float = 1.0


def probes() -> list[BProbe]:
    out: list[BProbe] = []
    out.extend(BProbe("substitute", s) for s in SUBSTITUTES)
    for lag in B_LAGS:
        out.append(BProbe("lag", "B", lag=lag))
    for amp in B_AMPS:
        out.append(BProbe("amplitude", "B", amplitude=amp))
    for sign in B_SIGNS:
        out.append(BProbe("sign", "B", sign=sign))
    out.extend((
        BProbe("hold", "B"),
        BProbe("randomize_within_world", "B"),
        BProbe("permute_across_world", "B"),
        BProbe("phase_shuffle", "B"),
        BProbe("time_reverse", "B"),
    ))
    return out


if __name__ == "__main__":
    ps = probes()
    print(f"B probes={len(ps)}")
    print("substitutes=" + ",".join(SUBSTITUTES))
