"""Research-only causal memory features for historical TIAMAT replay.

These features reconstruct *available-at-timestamp* memory from observed
historical columns. They do not assert hidden TIAMAT state and do not grant
runtime authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Iterable, Mapping


@dataclass(frozen=True)
class MemoryPoint:
    age_h: float
    freshness: float
    pressure_delta: float
    pressure_ema: float
    deficit_ema: float
    shock_ema: float
    recovery_ema: float


def _ema(values: list[float], alpha: float) -> float:
    if not values:
        return 0.0
    x = values[0]
    for value in values[1:]:
        x = alpha * value + (1.0 - alpha) * x
    return x


def causal_memory(history: Iterable[Mapping[str, float]], *, half_life_h: float = 24.0) -> MemoryPoint:
    """Summarize only prior/current observations; never reads future rows."""
    rows = list(history)
    if not rows:
        return MemoryPoint(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    pressure = [float(r.get("live_up_pressure_proxy", 0.0)) for r in rows]
    deficit = [float(r.get("LiveDeficit", 0.0)) for r in rows]
    shock = [float(r.get("SimpleShock", 0.0)) for r in rows]
    recovery = [float(r.get("RecoveryWeakness_v1", 0.0)) for r in rows]
    age = float(rows[-1].get("run_age_h_live", len(rows)))
    prev = pressure[-2] if len(pressure) > 1 else pressure[-1]
    alpha = 1.0 - exp(-1.0 / max(half_life_h, 1e-9))
    freshness = exp(-age / max(half_life_h, 1e-9))
    return MemoryPoint(
        age_h=age,
        freshness=freshness,
        pressure_delta=pressure[-1] - prev,
        pressure_ema=_ema(pressure, alpha),
        deficit_ema=_ema(deficit, alpha),
        shock_ema=_ema(shock, alpha),
        recovery_ema=_ema(recovery, alpha),
    )
