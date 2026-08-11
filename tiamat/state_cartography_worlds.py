"""Synthetic trajectory corpus for State Cartography forensic experiments.

This is deliberately separate from prediction labels in expanded_worlds.py.
The corpus supplies observable trajectories plus pre-existing dimensions so the
forensic layer can test whether similar present geometry implies similar futures.
It is synthetic evidence, not a claim about hidden real-world mechanisms.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class CartographyEpisode:
    world: str
    left: tuple[float, ...]
    right: tuple[float, ...]
    dimensions_left: Mapping[str, tuple[float, ...]]
    dimensions_right: Mapping[str, tuple[float, ...]]
    expected_missing: str | None


def _episode(world: str) -> CartographyEpisode:
    n = 40
    left = [0.0] * n
    right = [0.0] * n
    dims_l: dict[str, tuple[float, ...]] = {}
    dims_r: dict[str, tuple[float, ...]] = {}
    expected = None

    if world == "near_miss":
        # Same observed trajectory now; resistance differs before the futures
        # separate. The fingerprint cannot see that dimension directly.
        for i in range(8, n):
            left[i] = max(0.0, 1.0 - 0.06 * (i - 8))
            right[i] = max(0.0, 1.0 - 0.06 * (i - 8))
        resistance_l = [0.0] * n
        resistance_r = [0.0] * n
        for i in range(5, n):
            resistance_r[i] = 1.0
        for i in range(16, n):
            right[i] += 0.55 * (i - 15) / 24.0
        dims_l["resistance"] = tuple(resistance_l)
        dims_r["resistance"] = tuple(resistance_r)
        expected = "resistance"

    elif world == "decelerating":
        for i in range(8, n):
            t = i - 8
            left[i] = t * 0.08 - 0.003 * t * t
            right[i] = t * 0.08 - 0.003 * t * t
        r_l = [0.0] * n
        r_r = [0.0] * n
        for i in range(4, n):
            r_r[i] = 0.8
        for i in range(18, n):
            right[i] -= 0.04 * (i - 17)
        dims_l["residual_load"] = tuple(r_l)
        dims_r["residual_load"] = tuple(r_r)
        expected = "residual_load"

    elif world == "proximity_with_resistance":
        for i in range(8, n):
            t = i - 8
            left[i] = 1.0 - 0.045 * t
            right[i] = 1.0 - 0.045 * t
        c_l = [0.0] * n
        c_r = [0.0] * n
        for i in range(5, n):
            c_r[i] = 1.0
        for i in range(20, n):
            right[i] += 0.025 * (i - 19) ** 1.2
        dims_l["coupling"] = tuple(c_l)
        dims_r["coupling"] = tuple(c_r)
        expected = "coupling"

    elif world == "overshoot":
        for i in range(8, n):
            t = i - 8
            base = min(1.0, t * 0.09)
            left[i] = base
            right[i] = base
        h_l = [0.0] * n
        h_r = [0.0] * n
        for i in range(5, n):
            h_r[i] = 1.0
        for i in range(17, n):
            right[i] += 0.08 * (i - 16)
        dims_l["hysteresis"] = tuple(h_l)
        dims_r["hysteresis"] = tuple(h_r)
        expected = "hysteresis"

    elif world == "reversal_after_acceleration":
        for i in range(8, n):
            t = i - 8
            base = 0.02 * t * t
            left[i] = base
            right[i] = base
        p_l = [0.0] * n
        p_r = [0.0] * n
        for i in range(5, n):
            p_r[i] = 1.0
        for i in range(18, n):
            right[i] -= 0.06 * (i - 17)
        dims_l["phase"] = tuple(p_l)
        dims_r["phase"] = tuple(p_r)
        expected = "phase"

    else:
        # Control: identical future. This establishes the consistent-future
        # path without using labels or mechanism names.
        for i in range(8, n):
            t = i - 8
            left[i] = right[i] = 0.02 * t

    return CartographyEpisode(world, tuple(left), tuple(right), dims_l, dims_r, expected)


def build_forensic_episodes() -> tuple[CartographyEpisode, ...]:
    names = (
        "near_miss",
        "decelerating",
        "proximity_with_resistance",
        "overshoot",
        "reversal_after_acceleration",
        "control_consistent",
    )
    return tuple(_episode(name) for name in names)
