"""Diagnostic benchmark: canonical TIAMAT state versus reduced D/V/B.

This module is deliberately non-authoritative. It never replaces the canonical
TIAMAT state machine. It provides a deterministic comparison harness for asking
whether a reduced D/V/B representation preserves predictive information carried
by the richer state *and its temporal accumulation*.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping, Sequence

from .state import TiamatState


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    """One frozen observation with a binary downstream target."""

    B: float
    V: float
    D: float
    recovery: float
    residual_load: float
    momentum: float
    pressure: float
    hazard_raw: float
    target: int

    def __post_init__(self) -> None:
        values = (self.B, self.V, self.D, self.recovery, self.residual_load,
                  self.momentum, self.pressure, self.hazard_raw)
        if not all(isfinite(float(x)) for x in values):
            raise ValueError("benchmark values must be finite")
        if int(self.target) not in (0, 1):
            raise ValueError("target must be binary")

    @classmethod
    def from_state(cls, state: TiamatState, target: int) -> "BenchmarkRow":
        """Build the row from the actual canonical TIAMAT state object."""
        return cls(
            B=float(state.B),
            V=float(state.V),
            D=float(state.D),
            recovery=float(state.recovery),
            residual_load=float(state.residual_load),
            momentum=float(state.momentum),
            pressure=float(state.pressure),
            hazard_raw=float(state.D + state.pressure),
            target=int(target),
        )

    @classmethod
    def from_mapping(cls, row: Mapping[str, object], target_key: str = "target") -> "BenchmarkRow":
        """Adapt a serialized canonical state/row without changing its values."""
        state = TiamatState.from_mapping(row)
        return cls.from_state(state, int(row[target_key]))


@dataclass(frozen=True, slots=True)
class FeatureComparison:
    """Simple deterministic separation score for one representation."""

    name: str
    mean_positive: float
    mean_negative: float
    separation: float
    n: int


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _score(name: str, rows: Sequence[BenchmarkRow], feature) -> FeatureComparison:
    positives = [float(feature(r)) for r in rows if r.target == 1]
    negatives = [float(feature(r)) for r in rows if r.target == 0]
    if not positives or not negatives:
        raise ValueError("benchmark requires both target classes")
    pos = _mean(positives)
    neg = _mean(negatives)
    return FeatureComparison(name, pos, neg, abs(pos - neg), len(rows))


def compare_dvb(rows: Iterable[BenchmarkRow]) -> tuple[FeatureComparison, ...]:
    """Compare instantaneous D/V/B and derived projections.

    Scores are descriptive only. No thresholds are tuned here.
    """
    frozen = tuple(rows)
    if len(frozen) < 2:
        raise ValueError("at least two observations are required")
    return (
        _score("B", frozen, lambda r: r.B),
        _score("V", frozen, lambda r: r.V),
        _score("D", frozen, lambda r: r.D),
        _score("DVB", frozen, lambda r: abs(r.B) + abs(r.V) + abs(r.D)),
        _score("recovery", frozen, lambda r: r.recovery),
        _score("residual_load", frozen, lambda r: r.residual_load),
        _score("momentum", frozen, lambda r: r.momentum),
        _score("pressure", frozen, lambda r: r.pressure),
        _score("hazard_raw", frozen, lambda r: r.hazard_raw),
    )


def _history_feature(rows: Sequence[BenchmarkRow], name: str, feature, horizon: int) -> FeatureComparison:
    if horizon < 1:
        raise ValueError("horizon must be positive")
    if len(rows) <= horizon:
        raise ValueError("history requires more observations than the horizon")
    values = []
    targets = []
    for i in range(horizon, len(rows)):
        window = rows[i - horizon:i + 1]
        values.append(sum(float(feature(r)) for r in window) / len(window))
        targets.append(rows[i].target)
    positives = [v for v, t in zip(values, targets) if t == 1]
    negatives = [v for v, t in zip(values, targets) if t == 0]
    if not positives or not negatives:
        raise ValueError("benchmark history requires both target classes")
    pos = _mean(positives)
    neg = _mean(negatives)
    return FeatureComparison(name, pos, neg, abs(pos - neg), len(values))


def compare_dvb_history(rows: Iterable[BenchmarkRow], horizon: int = 3) -> tuple[FeatureComparison, ...]:
    """Compare accumulated histories of D, V, B and the combined representation.

    This is intentionally a simple, fixed-window diagnostic. It tests whether
    temporal accumulation carries information that instantaneous D/V/B misses;
    it does not fit or optimize a predictive model.
    """
    frozen = tuple(rows)
    return (
        _history_feature(frozen, f"B_history_{horizon}", lambda r: r.B, horizon),
        _history_feature(f"V_history_{horizon}", lambda r: r.V, horizon),
        _history_feature(f"D_history_{horizon}", lambda r: r.D, horizon),
        _history_feature(
            frozen, f"DVB_history_{horizon}",
            lambda r: abs(r.B) + abs(r.V) + abs(r.D), horizon,
        ),
    )
