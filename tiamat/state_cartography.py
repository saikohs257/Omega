from __future__ import annotations

from math import sqrt
from typing import Sequence, Any


def fingerprint(values: Sequence[Any]) -> tuple[float, ...]:
    """Return a current-state fingerprint without looking into the future.

    The fingerprint is deliberately a lossless numeric tuple for the supplied
    state sequence.  Consumers decide how much of it represents the current
    state; this module does not encode future observations into similarity.
    """
    return tuple(float(value) for value in values)


def current_distance(a: Any, b: Any) -> float:
    """Measure distance between two current-state fingerprints."""
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        if len(a) != len(b):
            raise ValueError("fingerprints must have equal length")
        return sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))
    return abs(float(a) - float(b))
