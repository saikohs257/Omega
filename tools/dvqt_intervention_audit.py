"""Counterfactual DVQT intervention design.

Separates the additive generator from apparent interactions induced by
thresholding.  The audit compares additive, interaction, proxy, delayed,
phase-gated and noise-B worlds under identical scoring rules.
"""
from __future__ import annotations

from dataclasses import dataclass

WORLDS = (
    "additive_dvb",
    "additive_dv",
    "dv_plus_dv_interaction",
    "b_as_dv_proxy",
    "b_delayed",
    "b_phase_gated",
    "b_noise",
)

WEIGHTS = (0.45, 0.35, 0.20)
B_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
PHASES = ("early", "mid", "late", "high", "low")
LAGS = tuple(range(-5, 6))

@dataclass(frozen=True)
class Intervention:
    world: str
    d: float
    v: float
    b: float
    phase: str = "mid"
    lag: int = 0


def target_score(d: float, v: float, b: float) -> float:
    return WEIGHTS[0] * d + WEIGHTS[1] * v + WEIGHTS[2] * b


def threshold_target(d: float, v: float, b: float) -> int:
    return int(target_score(d, v, b) >= 0.5)


def b_sweep(d: float, v: float) -> list[Intervention]:
    return [Intervention("additive_dvb", d, v, b) for b in B_LEVELS]


def probes() -> list[Intervention]:
    out: list[Intervention] = []
    for world in WORLDS:
        out.extend(Intervention(world, d, v, b) for d, v, b in ((0.2,0.2,0.0),(0.8,0.2,0.0),(0.2,0.8,0.0),(0.8,0.8,1.0)))
    for d, v in ((0.2,0.2),(0.2,0.8),(0.8,0.2),(0.8,0.8)):
        out.extend(b_sweep(d, v))
    out.extend(Intervention("phase_sweep", 0.6, 0.6, 0.5, phase=p) for p in PHASES)
    out.extend(Intervention("lag_sweep", 0.6, 0.6, 0.5, lag=l) for l in LAGS)
    return out


if __name__ == "__main__":
    ps = probes()
    print(f"intervention_probes={len(ps)}")
    print(f"worlds={','.join(WORLDS)}")
    print(f"B_levels={B_LEVELS}")
    print(f"lags={LAGS}")
