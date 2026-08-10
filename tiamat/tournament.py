"""Bounded tournament orchestration for TIAMAT candidate combinations.

This layer coordinates combination-search evaluation over held-out evidence.
It does not promote any candidate into canonical state; it only packages the
search result and the selected evidence-driven decision for downstream review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .candidate_library import DEFAULT_CANDIDATE_MODELS
from .combination_search import CombinationSearchReport, run_combination_search
from .model_selection import ModelSelector, SelectionDecision


@dataclass(frozen=True, slots=True)
class TournamentCase:
    """One held-out scenario to score against the candidate library."""

    name: str
    labels: tuple[int, ...]
    heldout_predictions: Mapping[str, Sequence[float]]
    stability: Mapping[str, float] = field(default_factory=dict)
    max_size: int = 4

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be non-empty")
        if not self.labels:
            raise ValueError("labels must be non-empty")
        if self.max_size < 1:
            raise ValueError("max_size must be positive")


@dataclass(frozen=True, slots=True)
class TournamentResult:
    """Search report + selected decision for one case."""

    case_name: str
    report: CombinationSearchReport
    decision: SelectionDecision

    @property
    def best_model_id(self) -> str | None:
        best = self.report.best
        return None if best is None else best.spec.model_id


@dataclass(frozen=True, slots=True)
class TournamentRunner:
    """Deterministic bounded search runner over the candidate library."""

    selector: ModelSelector = field(default_factory=ModelSelector)
    specs: tuple = DEFAULT_CANDIDATE_MODELS

    def run_case(self, case: TournamentCase) -> TournamentResult:
        report = run_combination_search(
            self.specs,
            case.heldout_predictions,
            case.labels,
            stability=case.stability,
            max_size=case.max_size,
        )
        decision = self.selector.select(result.metrics for result in report.frontier)
        return TournamentResult(case_name=case.name, report=report, decision=decision)

    def run(self, cases: Sequence[TournamentCase]) -> tuple[TournamentResult, ...]:
        return tuple(self.run_case(case) for case in cases)
