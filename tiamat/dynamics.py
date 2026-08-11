"""Deterministic TIAMAT diagnostic dynamics.

This module exposes the recovered/experimental scalar dynamics as explicit,
inspectable functions.  It does not silently promote them into the canonical
state machine; callers can use the outputs as evidence for transition,
identification, replay, and tournament experiments.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log

_EPS = 1e-12


def sigmoid(x: float) -> float:
    x = float(x)
    if not isfinite(x):
        raise ValueError("x must be finite")
    if x >= 0.0:
        z = exp(-x)
        return 1.0 / (1.0 + z)
    z = exp(x)
    return z / (1.0 + z)


def logit(p: float) -> float:
    p = float(p)
    if not isfinite(p) or not 0.0 < p < 1.0:
        raise ValueError("p must be finite and strictly between 0 and 1")
    return log(p / (1.0 - p))


def robust_z(value: float, median: float, mad: float) -> float:
    """Robust standardized value using MAD with a deterministic epsilon floor."""
    value, median, mad = map(float, (value, median, mad))
    if not all(isfinite(x) for x in (value, median, mad)):
        raise ValueError("robust_z inputs must be finite")
    scale = max(abs(mad), _EPS)
    return (value - median) / scale


def simple_shock(*, abs_ret: float, rv24: float, range_pct: float, log_qv: float, imb_abs: float, medians: tuple[float, ...], mads: tuple[float, ...]) -> float:
    """Compute the five-signal robust SimpleShock score.

    The inputs are independently robust-standardized and averaged before the
    logistic squashing step.  Windowing/rolling statistics remain upstream so
    this function is deterministic and free of hidden look-ahead.
    """
    values = (abs_ret, rv24, range_pct, log_qv, imb_abs)
    if len(medians) != 5 or len(mads) != 5:
        raise ValueError("SimpleShock requires five medians and five MADs")
    z = [robust_z(v, m, d) for v, m, d in zip(values, medians, mads)]
    return sigmoid(sum(z) / len(z))


def live_deficit_update(previous: float, ret_1h_pct: float, simple_shock: float, robust24h_downside: float) -> float:
    """Apply the recovered LiveDeficit recurrence for one observation."""
    previous = float(previous)
    if not 0.0 < previous < 1.0:
        raise ValueError("previous LiveDeficit must be in (0, 1)")
    shock = float(simple_shock)
    downside = float(robust24h_downside)
    ret = float(ret_1h_pct)
    if not all(isfinite(x) for x in (shock, downside, ret)) or not 0.0 <= shock <= 1.0:
        raise ValueError("LiveDeficit inputs are invalid")
    value = (
        0.952 * logit(previous)
        + 0.367 * max(0.0, -ret)
        - 0.232 * max(0.0, ret)
        + 0.057 * shock
        + 2.431 * max(0.0, shock - 0.70)
        - 0.074 * downside
        - 0.068
    )
    return sigmoid(value)


def hazard_score(hazard_raw: float) -> float:
    """Map hazard_raw through the recovered 1.8-centered sigmoid."""
    return sigmoid(float(hazard_raw) - 1.8)


def residual_load(damage: float, recovery: float) -> float:
    damage, recovery = float(damage), float(recovery)
    if not all(isfinite(x) for x in (damage, recovery)):
        raise ValueError("damage and recovery must be finite")
    return max(0.0, damage - recovery)


@dataclass(frozen=True, slots=True)
class DynamicsSnapshot:
    """Single timestamp diagnostic bundle used by the full-state experiments."""

    simple_shock: float
    live_deficit: float
    recovery: float
    residual_load: float
    momentum: float
    pressure: float
    hazard_raw: float
    hazard_score: float

    def __post_init__(self) -> None:
        for name in ("simple_shock", "live_deficit", "recovery", "residual_load", "momentum", "pressure", "hazard_raw", "hazard_score"):
            if not isfinite(float(getattr(self, name))):
                raise ValueError(f"{name} must be finite")
        for name in ("simple_shock", "live_deficit", "hazard_score"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
