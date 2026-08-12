"""Evidence-gated candidate model selection for TIAMAT.

Candidate features remain hypotheses until held-out evidence supports them.
Selection reports discrimination, calibration, log loss, stability and
complexity; disagreement can remain UNRESOLVED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, log
from typing import Iterable, Mapping, Sequence

from runtime.selection import SelectionThresholds

_EPS = 1e-12


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    model_id: str
    features: tuple[str, ...]
    complexity: int | None = None
    family: str = "candidate"

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        if not self.features:
            raise ValueError("features must be non-empty")
        if len(set(self.features)) != len(self.features):
            raise ValueError("features must be unique")
        if self.complexity is not None and self.complexity < 1:
            raise ValueError("complexity must be positive")

    @property
    def size(self) -> int:
        return self.complexity if self.complexity is not None else len(self.features)


@dataclass(frozen=True, slots=True)
class ModelMetrics:
    model_id: str
    auc: float
    brier: float
    log_loss: float
    stability: float = 1.0
    complexity: int = 1
    evaluated_n: int = 0
    score: float = 0.0
    calibration_error: float = 0.0
    brier_skill: float = 0.0

    def __post_init__(self) -> None:
        for name in ("auc", "brier", "log_loss", "stability", "score", "calibration_error", "brier_skill"):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.auc <= 1.0:
            raise ValueError("auc must be in [0, 1]")
        if not 0.0 <= self.brier <= 1.0:
            raise ValueError("brier must be in [0, 1]")
        if self.log_loss < 0.0:
            raise ValueError("log_loss cannot be negative")
        if not 0.0 <= self.stability <= 1.0:
            raise ValueError("stability must be in [0, 1]")
        if not 0.0 <= self.calibration_error <= 1.0:
            raise ValueError("calibration_error must be in [0, 1]")
        if self.complexity < 1:
            raise ValueError("complexity must be positive")
        if self.evaluated_n < 0:
            raise ValueError("evaluated_n cannot be negative")


def brier_score(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    _validate_observations(probabilities, labels)
    return sum((float(p) - int(y)) ** 2 for p, y in zip(probabilities, labels)) / len(probabilities)


def brier_skill_score(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    """Return improvement over the prevalence-only Brier baseline."""
    _validate_observations(probabilities, labels)
    prevalence = sum(int(y) for y in labels) / len(labels)
    baseline = prevalence * (1.0 - prevalence)
    if baseline <= _EPS:
        return 0.0
    return 1.0 - brier_score(probabilities, labels) / baseline


def log_loss(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    _validate_observations(probabilities, labels)
    total = 0.0
    for p, y in zip(probabilities, labels):
        p = min(1.0 - _EPS, max(_EPS, float(p)))
        y = int(y)
        total -= y * log(p) + (1 - y) * log(1.0 - p)
    return total / len(probabilities)


def binary_auc(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    _validate_observations(probabilities, labels)
    positives = sum(int(y) for y in labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("AUC requires both positive and negative labels")
    ordered = sorted(zip(map(float, probabilities), map(int, labels)), key=lambda x: x[0])
    rank_sum = 0.0
    i = 0
    rank = 1
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        avg_rank = (rank + rank + (j - i) - 1) / 2.0
        rank_sum += avg_rank * sum(y for _, y in ordered[i:j])
        rank += j - i
        i = j
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def calibration_error(probabilities: Sequence[float], labels: Sequence[int], *, bins: int = 10) -> float:
    """Return equal-width expected calibration error; lower is better."""
    _validate_observations(probabilities, labels)
    if bins < 1:
        raise ValueError("bins must be positive")
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, y in zip(probabilities, labels):
        pf = float(p)
        idx = min(bins - 1, int(pf * bins))
        buckets[idx].append((pf, int(y)))
    n = len(probabilities)
    error = 0.0
    for bucket in buckets:
        if bucket:
            error += len(bucket) / n * abs(
                sum(p for p, _ in bucket) / len(bucket)
                - sum(y for _, y in bucket) / len(bucket)
            )
    return error


def composite_score(*, auc: float, brier: float, log_loss_value: float, stability: float, complexity: int, calibration_error_value: float = 0.0, brier_skill: float = 0.0) -> float:
    complexity_penalty = 0.01 * max(0, complexity - 1)
    return 0.30 * auc + 0.20 * (1.0 - brier) + 0.15 * (1.0 / (1.0 + log_loss_value)) + 0.15 * (1.0 - calibration_error_value) + 0.10 * stability + 0.10 * max(0.0, brier_skill) - complexity_penalty


def evaluate_candidate(spec: CandidateSpec, probabilities: Sequence[float], labels: Sequence[int], *, stability: float = 1.0) -> ModelMetrics:
    auc = binary_auc(probabilities, labels)
    brier = brier_score(probabilities, labels)
    ll = log_loss(probabilities, labels)
    ece = calibration_error(probabilities, labels)
    skill = brier_skill_score(probabilities, labels)
    score = composite_score(auc=auc, brier=brier, log_loss_value=ll, stability=stability, complexity=spec.size, calibration_error_value=ece, brier_skill=skill)
    return ModelMetrics(spec.model_id, auc, brier, ll, stability, spec.size, len(labels), score, ece, skill)


def dominates(a: ModelMetrics, b: ModelMetrics) -> bool:
    no_worse = a.auc >= b.auc and a.brier <= b.brier and a.log_loss <= b.log_loss and a.stability >= b.stability and a.calibration_error <= b.calibration_error and a.brier_skill >= b.brier_skill and a.complexity <= b.complexity
    strictly_better = a.auc > b.auc or a.brier < b.brier or a.log_loss < b.log_loss or a.stability > b.stability or a.calibration_error < b.calibration_error or a.brier_skill > b.brier_skill or a.complexity < b.complexity
    return no_worse and strictly_better


def pareto_front(metrics: Iterable[ModelMetrics]) -> tuple[ModelMetrics, ...]:
    items = tuple(metrics)
    return tuple(sorted((m for m in items if not any(dominates(o, m) for o in items if o is not m)), key=lambda m: m.model_id))


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    status: str
    selected_model_id: str | None
    score: float
    reason: str
    candidates: tuple[str, ...] = field(default_factory=tuple)


class ModelSelector:
    def __init__(
        self,
        *,
        selection_thresholds: SelectionThresholds | None = None,
        min_auc: float | None = None,
        max_brier: float = 0.25,
        min_stability: float = 0.0,
        max_calibration_error: float | None = None,
        min_brier_skill: float | None = None,
    ) -> None:
        """Select candidates using the canonical frozen selection contract.

        Legacy threshold arguments remain accepted for compatibility. When
        supplied, they construct an explicit SelectionThresholds instance;
        otherwise the canonical default contract is used.
        """
        if selection_thresholds is not None and any(
            value is not None for value in (min_auc, max_calibration_error, min_brier_skill)
        ):
            raise ValueError("selection_thresholds cannot be combined with legacy selection thresholds")
        if selection_thresholds is None:
            selection_thresholds = SelectionThresholds(
                auc_min=0.5 if min_auc is None else float(min_auc),
                ece_max=0.10 if max_calibration_error is None else float(max_calibration_error),
                brier_skill_min=0.05 if min_brier_skill is None else float(min_brier_skill),
            )
        self.selection_thresholds = selection_thresholds
        self.min_auc = selection_thresholds.auc_min
        self.max_brier = float(max_brier)
        self.min_stability = float(min_stability)
        self.max_calibration_error = selection_thresholds.ece_max
        self.min_brier_skill = selection_thresholds.brier_skill_min

    def select(self, metrics: Iterable[ModelMetrics]) -> SelectionDecision:
        items = tuple(metrics)
        if not items:
            return SelectionDecision("UNRESOLVED", None, 0.0, "no candidates evaluated")
        eligible = tuple(
            m for m in items
            if m.auc > self.selection_thresholds.auc_min
            and m.brier < self.max_brier
            and m.stability > self.min_stability
            and m.calibration_error <= self.selection_thresholds.ece_max
            and m.brier_skill >= self.selection_thresholds.brier_skill_min
        )
        if not eligible:
            return SelectionDecision("UNRESOLVED", None, 0.0, "no candidate passed minimum evidence gates")
        front = pareto_front(eligible)
        best = max(front, key=lambda m: (m.score, m.auc, m.brier_skill, -m.brier, -m.log_loss, -m.complexity, m.model_id))
        return SelectionDecision("SELECTED", best.model_id, best.score, "best eligible nondominated candidate by composite evidence score", tuple(m.model_id for m in front))


def consensus(probabilities: Mapping[str, float], *, tolerance: float = 0.10) -> tuple[str, float, tuple[str, ...]]:
    if not probabilities:
        return "UNRESOLVED", 0.0, ()
    values = tuple(float(v) for v in probabilities.values())
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    if spread > tolerance:
        return "CONTESTED", mean, tuple(sorted(probabilities))
    return ("HIGH" if mean >= 0.5 else "LOW"), mean, tuple(sorted(probabilities))


def _validate_observations(probabilities: Sequence[float], labels: Sequence[int]) -> None:
    _check_lengths(probabilities, labels)
    if not probabilities:
        raise ValueError("at least one observation is required")
    for probability in probabilities:
        value = float(probability)
        if not isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("probabilities must be finite and in [0, 1]")
    for label in labels:
        if int(label) not in (0, 1) or label not in (0, 1):
            raise ValueError("labels must be binary")


def _check_lengths(probabilities: Sequence[float], labels: Sequence[int]) -> None:
    if len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must have equal length")
