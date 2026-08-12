"""Diagnostic benchmark: canonical TIAMAT variables versus reduced D/V/B.

This module is deliberately non-authoritative. It does not replace the
canonical TIAMAT state machine. It provides a deterministic comparison harness
for asking whether a reduced D/V/B representation preserves information carried
by the richer TIAMAT diagnostic bundle.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping, Sequence


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
    def from_mapping(cls, row: Mapping[str, object], target_key: str = "target") -> "BenchmarkRow":
        return cls(
            B=float(row["B"]), V=float(row["V"]), D=float(row["D"]),
            recovery=float(row.get("recovery", max(0.0, -float(row["V"]))),),
            residual_load=float(row.get("residual_load", max(0.0, float(row["D"]) - max(0.0, -float(row["V"]))),)),
            momentum=float(row.get("momentum", row["V"])),
            pressure=float(row.get("pressure", max(0.0, float(row["V"]))),),
            hazard_raw=float(row.get("hazard_raw", float(row["D"]) + max(0.0, float(row["V"]))),),
            target=int(row[target_key]),
        )


@dataclass(frozen=True, slots=True)
class FeatureComparison:
    """Simple deterministic separation score for one feature set."""

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
    """Compare D, V, B and their reduced residual/recovery projections.

    The returned scores are descriptive only. No thresholds are tuned here.
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
