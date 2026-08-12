"""Benchmark observed TIAMAT memory features against instantaneous baselines.

Research-only. This module operates on timestamp-ordered observed replay rows and
never treats reconstructed memory as canonical TIAMAT state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .historical_memory import causal_memory


@dataclass(frozen=True)
class MemoryComparison:
    name: str
    values: tuple[float, ...]
    n: int


def _series(rows: list[Mapping[str, float]], key: str) -> tuple[float, ...]:
    return tuple(float(row.get(key, 0.0)) for row in rows)


def _memory_series(rows: list[Mapping[str, float]], *, half_life_h: float) -> tuple[dict[str, float], ...]:
    return tuple(causal_memory(rows[:i + 1], half_life_h=half_life_h).__dict__ for i in range(len(rows)))


def compare_instantaneous_and_memory(
    rows: Iterable[Mapping[str, float]], *, half_life_h: float = 24.0
) -> tuple[MemoryComparison, ...]:
    """Return timestamp-aligned observed and causal-memory feature series.

    No fitting or target inspection occurs here. The caller can apply a fixed
    downstream metric using a separately supplied target series.
    """
    frozen = list(rows)
    if not frozen:
        raise ValueError("at least one replay row is required")
    memory = _memory_series(frozen, half_life_h=half_life_h)
    return (
        MemoryComparison("live_up_pressure_proxy", _series(frozen, "live_up_pressure_proxy"), len(frozen)),
        MemoryComparison("LiveDeficit", _series(frozen, "LiveDeficit"), len(frozen)),
        MemoryComparison("SimpleShock", _series(frozen, "SimpleShock"), len(frozen)),
        MemoryComparison("RecoveryWeakness_v1", _series(frozen, "RecoveryWeakness_v1"), len(frozen)),
        MemoryComparison("freshness", tuple(float(point["freshness"]) for point in memory), len(frozen)),
        MemoryComparison("pressure_ema", tuple(float(point["pressure_ema"]) for point in memory), len(frozen)),
        MemoryComparison("deficit_ema", tuple(float(point["deficit_ema"]) for point in memory), len(frozen)),
        MemoryComparison("shock_ema", tuple(float(point["shock_ema"]) for point in memory), len(frozen)),
        MemoryComparison("recovery_ema", tuple(float(point["recovery_ema"]) for point in memory), len(frozen)),
        MemoryComparison("pressure_delta", tuple(float(point["pressure_delta"]) for point in memory), len(frozen)),
        MemoryComparison("run_age_h_live", _series(frozen, "run_age_h_live"), len(frozen)),
    )
