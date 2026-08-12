"""Target-aware metric discovery for TIAMAT experiments.

This module deliberately does not declare Brier, LogLoss, or AUC as the
universal primary metric. It evaluates a metric panel against an explicit
prediction target so Omega can test which notion of predictive value is
appropriate instead of assuming it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite, log
from typing import Sequence

from .model_selection import binary_auc, brier_score, calibration_error, log_loss


class TargetKind(str, Enum):
    EVENT = "event"
    HIDDEN_STATE = "hidden_state"
    TIME_TO_TRANSITION = "time_to_transition"
    TRAJECTORY = "trajectory"
    GUARD_OR_MODE = "guard_or_mode"


@dataclass(frozen=True, slots=True)
class MetricObservation:
    name: str
    value: float
    direction: str
    target: TargetKind
    interpretation: str

    def __post_init__(self) -> None:
        if self.direction not in {"higher", "lower"}:
            raise ValueError("direction must be 'higher' or 'lower'")
        if not isfinite(float(self.value)):
            raise ValueError("metric value must be finite")


@dataclass(frozen=True, slots=True)
class MetricProfile:
    target: TargetKind
    observations: tuple[MetricObservation, ...]
    unresolved: bool
    reason: str

    @property
    def by_name(self) -> dict[str, MetricObservation]:
        return {item.name: item for item in self.observations}


def binary_metric_profile(
    probabilities: Sequence[float],
    labels: Sequence[int],
    *,
    target: TargetKind = TargetKind.EVENT,
) -> MetricProfile:
    """Build a metric panel for a binary target; no metric is primary."""
    if target == TargetKind.HIDDEN_STATE:
        raise ValueError("hidden_state requires multiclass probabilities")
    observations = (
        MetricObservation("auc", binary_auc(probabilities, labels), "higher", target, "discrimination/ranking"),
        MetricObservation("brier", brier_score(probabilities, labels), "lower", target, "probability accuracy"),
        MetricObservation("log_loss", log_loss(probabilities, labels), "lower", target, "probability sharpness and correctness"),
        MetricObservation("calibration_error", calibration_error(probabilities, labels), "lower", target, "probability calibration"),
    )
    return MetricProfile(target, observations, False, "metric panel only; no primary metric assumed")


def multiclass_brier(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> float:
    """Return the multiclass Brier score using vector squared error."""
    _validate_multiclass(probabilities, labels)
    total = 0.0
    for row, label in zip(probabilities, labels):
        total += sum((float(p) - (1.0 if j == int(label) else 0.0)) ** 2 for j, p in enumerate(row))
    return total / len(labels)


def multiclass_log_loss(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> float:
    """Return mean multiclass negative log likelihood."""
    _validate_multiclass(probabilities, labels)
    eps = 1e-12
    return -sum(log(max(eps, float(row[int(label)]))) for row, label in zip(probabilities, labels)) / len(labels)


def multiclass_accuracy(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> float:
    """Return top-1 state accuracy for a hidden-state target."""
    _validate_multiclass(probabilities, labels)
    correct = sum(max(range(len(row)), key=lambda i: row[i]) == int(label) for row, label in zip(probabilities, labels))
    return correct / len(labels)


def hidden_state_metric_profile(
    probabilities: Sequence[Sequence[float]], labels: Sequence[int]
) -> MetricProfile:
    observations = (
        MetricObservation("multiclass_brier", multiclass_brier(probabilities, labels), "lower", TargetKind.HIDDEN_STATE, "probability accuracy over latent states"),
        MetricObservation("multiclass_log_loss", multiclass_log_loss(probabilities, labels), "lower", TargetKind.HIDDEN_STATE, "belief quality over latent states"),
        MetricObservation("state_accuracy", multiclass_accuracy(probabilities, labels), "higher", TargetKind.HIDDEN_STATE, "top-1 state identification"),
    )
    return MetricProfile(TargetKind.HIDDEN_STATE, observations, False, "hidden-state metric panel; no primary metric assumed")


def metric_value_delta(reference: MetricObservation, candidate: MetricObservation) -> float:
    """Return signed improvement of candidate over reference."""
    if reference.name != candidate.name or reference.direction != candidate.direction:
        raise ValueError("observations must describe the same metric")
    return candidate.value - reference.value if reference.direction == "higher" else reference.value - candidate.value


def _validate_multiclass(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> None:
    if not probabilities or len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must be non-empty and aligned")
    classes = len(probabilities[0])
    if classes < 2:
        raise ValueError("at least two classes are required")
    for row, label in zip(probabilities, labels):
        if len(row) != classes or int(label) < 0 or int(label) >= classes:
            raise ValueError("invalid multiclass row or label")
        if any(not isfinite(float(p)) or float(p) < 0.0 for p in row):
            raise ValueError("probabilities must be finite and non-negative")
        if abs(sum(float(p) for p in row) - 1.0) > 1e-9:
            raise ValueError("each probability row must sum to one")
