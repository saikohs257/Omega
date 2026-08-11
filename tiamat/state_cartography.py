"""Trajectory-first state fingerprints for state-cartography experiments.

This module deliberately avoids mechanism labels. It summarizes observable
trajectories into a compact state representation and measures whether similar
current states have similar futures.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence


@dataclass(frozen=True, slots=True)
class StateFingerprint:
    value: float
    velocity: float
    acceleration: float


def _velocity(values: Sequence[float], alpha: float = 0.2) -> tuple[float, ...]:
    if not values:
        return ()
    out = [0.0]
    v = 0.0
    for prev, cur in zip(values, values[1:]):
        delta = float(cur) - float(prev)
        v = (1.0 - alpha) * v + alpha * delta
        out.append(v)
    return tuple(out)


def fingerprint(values: Sequence[float], *, alpha: float = 0.2) -> tuple[StateFingerprint, ...]:
    """Build per-time state fingerprints from one observable trajectory."""
    v = _velocity(values, alpha=alpha)
    a = _velocity(v, alpha=alpha)
    return tuple(
        StateFingerprint(float(x), float(vx), float(ax))
        for x, vx, ax in zip(values, v, a)
    )


def distance(a: StateFingerprint, b: StateFingerprint, *, value_weight: float = 1.0,
             velocity_weight: float = 1.0, acceleration_weight: float = 0.5) -> float:
    """Weighted Euclidean distance between instantaneous state fingerprints."""
    dv = value_weight * (a.value - b.value) ** 2
    dvel = velocity_weight * (a.velocity - b.velocity) ** 2
    dacc = acceleration_weight * (a.acceleration - b.acceleration) ** 2
    return sqrt(dv + dvel + dacc)


def future_distance(
    fingerprints_a: Sequence[StateFingerprint],
    fingerprints_b: Sequence[StateFingerprint],
    start: int,
    horizon: int = 4,
) -> float:
    """Compare future state trajectories from a common current-time index."""
    if start < 0 or start >= len(fingerprints_a) or start >= len(fingerprints_b):
        raise ValueError("start must fall inside both trajectories")
    end = min(start + horizon + 1, len(fingerprints_a), len(fingerprints_b))
    if end <= start + 1:
        return 0.0
    pairs = zip(fingerprints_a[start + 1 : end], fingerprints_b[start + 1 : end])
    values = [distance(x, y) for x, y in pairs]
    return sum(values) / len(values)


def current_distance(a: StateFingerprint, b: StateFingerprint) -> float:
    return distance(a, b)
