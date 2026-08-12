"""Small, deterministic helpers for comparing present state and future paths."""
from __future__ import annotations

from typing import Iterable


def fingerprint(state: Iterable[float]) -> tuple[float, ...]:
    """Return a stable, current-state fingerprint as a tuple of floats."""
    return tuple(float(value) for value in state)


def current_distance(left: float, right: float) -> float:
    """Distance between two scalar current-state components."""
    return abs(float(left) - float(right))
