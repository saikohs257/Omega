"""Bounded candidate-combination search for TIAMAT.

The search layer explores candidate combinations without promoting any feature
into canonical state. It uses staged expansion to avoid an unbounded power set:
seed models are evaluated first, then only candidates that improve the evidence
frontier are expanded.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence

from .model_selection import CandidateSpec, ModelMetrics, pareto_front


@dataclass(frozen=True, slots=True)
class CombinationResult:
    spec: CandidateSpec
    metrics: ModelMetrics


@dataclass(frozen=True, slots=True)
class CombinationSearchReport:
    evaluated: tuple[CombinationResult, ...]
    frontier: tuple[CombinationResult, ...]
    rejected: tuple[str, ...]

    @property
    def best(self) -> CombinationResult | None:
        if not self.frontier:
            return None
        return max(
            self.frontier,
            key=lambda r: (r.metrics.score, r.metrics.auc, -r.metrics.brier, -r.spec.size, r.spec.model_id),
        )


def staged_combinations(
    features: Sequence[str],
    *,
    max_size: int = 4,
) -> tuple[tuple[str, ...], ...]:
    """Return deterministic bounded combinations, excluding duplicates."""
    unique = tuple(dict.fromkeys(features))
    if max_size < 1:
        raise ValueError("max_size must be positive")
    return tuple(
        combo
        for size in range(1, min(max_size, len(unique)) + 1)
        for combo in combinations(unique, size)
    )


def select_evidence_frontier(results: Iterable[CombinationResult]) -> tuple[CombinationResult, ...]:
    """Return nondominated combination results."""
    items = tuple(results)
    front_metrics = pareto_front(result.metrics for result in items)
    ids = {metric.model_id for metric in front_metrics}
    return tuple(sorted((r for r in items if r.metrics.model_id in ids), key=lambda r: r.spec.model_id))


def run_combination_search(
    specs: Sequence[CandidateSpec],
    heldout_predictions: Mapping[str, Sequence[float]],
    labels: Sequence[int],
    *,
    stability: Mapping[str, float] | None = None,
    max_size: int = 4,
) -> CombinationSearchReport:
    """Score precomputed held-out predictions for bounded candidate models.

    Prediction generation/fitting intentionally lives outside this function so
    callers can enforce train/validation/test separation before evidence enters
    the selector.
    """
    from .model_selection import evaluate_candidate

    evaluated: list[CombinationResult] = []
    rejected: list[str] = []
    allowed = set(staged_combinations(tuple(f for s in specs for f in s.features), max_size=max_size))
    for spec in specs:
        if tuple(spec.features) not in allowed:
            rejected.append(spec.model_id)
            continue
        probabilities = heldout_predictions.get(spec.model_id)
        if probabilities is None:
            rejected.append(spec.model_id)
            continue
        metric = evaluate_candidate(spec, probabilities, labels, stability=(stability or {}).get(spec.model_id, 1.0))
        evaluated.append(CombinationResult(spec, metric))
    return CombinationSearchReport(tuple(evaluated), select_evidence_frontier(evaluated), tuple(sorted(rejected)))
