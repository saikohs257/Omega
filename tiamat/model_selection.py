"""Evidence-gated candidate model selection for TIAMAT.

This module deliberately does not decide what the canonical TIAMAT state is.
It provides a deterministic, leakage-resistant scoring layer for comparing
candidate observable/state combinations and for exposing model disagreement.

Design principles:
- candidate features remain available without becoming canonical state;
- evaluation data must be held out from selection;
- discrimination, calibration, log loss, stability and complexity are scored
  together rather than optimizing AUC alone;
- a candidate may be rejected when it is overconfident, unstable, or dominated;
- disagreement is first-class evidence and may yield an UNRESOLVED decision.

No third-party dependencies are required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log
from typing import Iterable, Mapping, Sequence


_EPS = 1e-12


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    """A candidate explanation/model surface.

    ``features`` are names from the broad observable library.  They are not
    automatically promoted to primitive state merely by appearing here.
    """

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
    """Out-of-sample metrics for one candidate.

    Higher is better for AUC and stability; lower is better for Brier, log loss,
    and complexity. ``score`` is deliberately conservative: it is a ranking aid,
    not a probability and not an authority claim.
    """

    model_id: str
    auc: float
    brier: float
    log_loss: float
    stability: float = 1.0
    complexity: int = 1
    evaluated_n: int = 0
    score: float = 0.0

    def __post_init__(self) -> None:
        for name in ("auc", "brier", "log_loss", "stability", "score"):
            value = float(getattr(self, name))
            if not value == value or value in (float("inf"), float("-inf")):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.auc <= 1.0:
            raise ValueError("auc must be in [0, 1]")
        if not 0.0 <= self.brier <= 1.0:
            raise ValueError("brier must be in [0, 1]")
        if self.log_loss < 0.0:
            raise ValueError("log_loss cannot be negative")
        if not 0.0 <= self.stability <= 1.0:
            raise ValueError("stability must be in [0, 1]")
        if self.complexity < 1:
            raise ValueError("complexity must be positive")
        if self.evaluated_n < 0:
            raise ValueError("evaluated_n cannot be negative")


def brier_score(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    """Return the binary Brier score; lower is better."""
    _check_lengths(probabilities, labels)
    if not probabilities:
        raise ValueError("at least one observation is required")
    return sum((float(p) - int(y)) ** 2 for p, y in zip(probabilities, labels)) / len(probabilities)


def log_loss(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    """Return binary log loss with bounded probabilities."""
    _check_lengths(probabilities, labels)
    if not probabilities:
        raise ValueError("at least one observation is required")
    total = 0.0
    for p, y in zip(probabilities, labels):
        p = min(1.0 - _EPS, max(_EPS, float(p)))
        y = int(y)
        if y not in (0, 1):
            raise ValueError("labels must be binary")
        total -= y * log(p) + (1 - y) * log(1.0 - p)
    return total / len(probabilities)


def binary_auc(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    """Compute ROC AUC using rank statistics; ties receive half credit."""
    _check_lengths(probabilities, labels)
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


def composite_score(
    *, auc: float, brier: float, log_loss_value: float, stability: float, complexity: int,
) -> float:
    """Conservative model-selection score; larger is better.

    The score intentionally rewards calibration and stability and applies a small
    complexity penalty. It must never be interpreted as a probability.
    """
    complexity_penalty = 0.01 * max(0, complexity - 1)
    return (
        0.40 * auc
        + 0.30 * (1.0 - brier)
        + 0.20 * (1.0 / (1.0 + log_loss_value))
        + 0.10 * stability
        - complexity_penalty
    )


def evaluate_candidate(
    spec: CandidateSpec,
    probabilities: Sequence[float],
    labels: Sequence[int],
    *,
    stability: float = 1.0,
) -> ModelMetrics:
    """Evaluate one candidate on already-held-out predictions."""
    auc = binary_auc(probabilities, labels)
    brier = brier_score(probabilities, labels)
    ll = log_loss(probabilities, labels)
    score = composite_score(
        auc=auc,
        brier=brier,
        log_loss_value=ll,
        stability=stability,
        complexity=spec.size,
    )
    return ModelMetrics(
        model_id=spec.model_id,
        auc=auc,
        brier=brier,
        log_loss=ll,
        stability=stability,
        complexity=spec.size,
        evaluated_n=len(labels),
        score=score,
    )


def dominates(a: ModelMetrics, b: ModelMetrics) -> bool:
    """Return whether ``a`` Pareto-dominates ``b`` on the core metrics."""
    no_worse = (
        a.auc >= b.auc
        and a.brier <= b.brier
        and a.log_loss <= b.log_loss
        and a.stability >= b.stability
        and a.complexity <= b.complexity
    )
    strictly_better = (
        a.auc > b.auc
        or a.brier < b.brier
        or a.log_loss < b.log_loss
        or a.stability > b.stability
        or a.complexity < b.complexity
    )
    return no_worse and strictly_better


def pareto_front(metrics: Iterable[ModelMetrics]) -> tuple[ModelMetrics, ...]:
    """Return nondominated candidates in deterministic model-id order."""
    items = tuple(metrics)
    return tuple(sorted((m for m in items if not any(dominates(o, m) for o in items if o is not m)), key=lambda m: m.model_id))


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    """Decision emitted by the selector."""

    status: str
    selected_model_id: str | None
    score: float
    reason: str
    candidates: tuple[str, ...] = field(default_factory=tuple)


class ModelSelector:
    """Deterministic selector with an explicit unresolved outcome."""

    def __init__(self, *, min_auc: float = 0.5, max_brier: float = 0.25, min_stability: float = 0.0) -> None:
        self.min_auc = float(min_auc)
        self.max_brier = float(max_brier)
        self.min_stability = float(min_stability)

    def select(self, metrics: Iterable[ModelMetrics]) -> SelectionDecision:
        items = tuple(metrics)
        if not items:
            return SelectionDecision("UNRESOLVED", None, 0.0, "no candidates evaluated")
        eligible = tuple(
            m for m in items
            if m.auc >= self.min_auc and m.brier <= self.max_brier and m.stability >= self.min_stability
        )
        if not eligible:
            return SelectionDecision("UNRESOLVED", None, 0.0, "no candidate passed minimum evidence gates")
        front = pareto_front(eligible)
        best = max(front, key=lambda m: (m.score, m.auc, -m.brier, -m.log_loss, -m.complexity, m.model_id))
        return SelectionDecision(
            "SELECTED",
            best.model_id,
            best.score,
            "best eligible nondominated candidate by composite score",
            tuple(m.model_id for m in front),
        )


def consensus(probabilities: Mapping[str, float], *, tolerance: float = 0.10) -> tuple[str, float, tuple[str, ...]]:
    """Return HIGH/LOW/CONTESTED consensus without forcing a decision."""
    if not probabilities:
        return "UNRESOLVED", 0.0, ()
    values = tuple(float(v) for v in probabilities.values())
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    if spread > tolerance:
        return "CONTESTED", mean, tuple(sorted(probabilities))
    return ("HIGH" if mean >= 0.5 else "LOW"), mean, tuple(sorted(probabilities))


def _check_lengths(probabilities: Sequence[float], labels: Sequence[int]) -> None:
    if len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must have equal length")
