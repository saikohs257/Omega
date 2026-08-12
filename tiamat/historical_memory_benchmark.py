"""Benchmark observed TIAMAT memory features against instantaneous baselines.

Research-only. This module operates on timestamp-ordered observed replay rows and
never treats reconstructed memory as canonical TIAMAT state.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Iterable, Mapping

from .historical_memory import MemoryPoint, _ema


@dataclass(frozen=True)
class MemoryComparison:
    name: str
    values: tuple[float, ...]
    n: int


def _series(rows: list[Mapping[str, float]], key: str) -> tuple[float, ...]:
    return tuple(float(row.get(key, 0.0)) for row in rows)


def _memory_series(
    rows: list[Mapping[str, float]],
    *,
    half_life_h: float,
    group_key: str | None,
) -> tuple[MemoryPoint, ...]:
    """Build causal memory incrementally, resetting at explicit run boundaries."""
    if not rows:
        return ()
    alpha = 1.0 - exp(-1.0 / max(half_life_h, 1e-9))
    result: list[MemoryPoint] = []
    previous_group = object()
    pressure_hist: list[float] = []
    deficit_hist: list[float] = []
    shock_hist: list[float] = []
    recovery_hist: list[float] = []

    for row in rows:
        group = row.get(group_key) if group_key else None
        if group != previous_group:
            pressure_hist = []
            deficit_hist = []
            shock_hist = []
            recovery_hist = []
            previous_group = group

        pressure = float(row.get("live_up_pressure_proxy", 0.0))
        deficit = float(row.get("LiveDeficit", 0.0))
        shock = float(row.get("SimpleShock", 0.0))
        recovery = float(row.get("RecoveryWeakness_v1", 0.0))
        prev_pressure = pressure_hist[-1] if pressure_hist else pressure

        pressure_hist.append(pressure)
        deficit_hist.append(deficit)
        shock_hist.append(shock)
        recovery_hist.append(recovery)

        age = float(row.get("run_age_h_live", len(pressure_hist)))
        freshness = exp(-age / max(half_life_h, 1e-9))
        result.append(
            MemoryPoint(
                age_h=age,
                freshness=freshness,
                pressure_delta=pressure - prev_pressure,
                pressure_ema=_ema(pressure_hist, alpha),
                deficit_ema=_ema(deficit_hist, alpha),
                shock_ema=_ema(shock_hist, alpha),
                recovery_ema=_ema(recovery_hist, alpha),
            )
        )
    return tuple(result)


def compare_instantaneous_and_memory(
    rows: Iterable[Mapping[str, float]], *, half_life_h: float = 24.0,
    group_key: str | None = "strict_run_id",
) -> tuple[MemoryComparison, ...]:
    """Return timestamp-aligned observed and causal-memory feature series.

    No fitting or target inspection occurs here. Memory resets whenever
    ``group_key`` changes, preventing state from crossing historical run
    boundaries. The caller can apply a fixed downstream metric using a
    separately supplied target series.
    """
    frozen = list(rows)
    if not frozen:
        raise ValueError("at least one replay row is required")
    memory = _memory_series(frozen, half_life_h=half_life_h, group_key=group_key)
    return (
        MemoryComparison("live_up_pressure_proxy", _series(frozen, "live_up_pressure_proxy"), len(frozen)),
        MemoryComparison("LiveDeficit", _series(frozen, "LiveDeficit"), len(frozen)),
        MemoryComparison("SimpleShock", _series(frozen, "SimpleShock"), len(frozen)),
        MemoryComparison("RecoveryWeakness_v1", _series(frozen, "RecoveryWeakness_v1"), len(frozen)),
        MemoryComparison("freshness", tuple(point.freshness for point in memory), len(frozen)),
        MemoryComparison("pressure_ema", tuple(point.pressure_ema for point in memory), len(frozen)),
        MemoryComparison("deficit_ema", tuple(point.deficit_ema for point in memory), len(frozen)),
        MemoryComparison("shock_ema", tuple(point.shock_ema for point in memory), len(frozen)),
        MemoryComparison("recovery_ema", tuple(point.recovery_ema for point in memory), len(frozen)),
        MemoryComparison("pressure_delta", tuple(point.pressure_delta for point in memory), len(frozen)),
        MemoryComparison("run_age_h_live", _series(frozen, "run_age_h_live"), len(frozen)),
    )
