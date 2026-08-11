"""Adversarial elimination with complete, auditable variant evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model_selection import CandidateSpec, ModelMetrics, ModelSelector
from .tournament import TournamentCase, TournamentRunner


@dataclass(frozen=True, slots=True)
class EliminationVariant:
    name: str
    predictions: Mapping[str, Sequence[float]]


@dataclass(frozen=True, slots=True)
class VariantAudit:
    variant: str
    selected: str | None
    status: str
    metrics: tuple[ModelMetrics, ...]


@dataclass(frozen=True, slots=True)
class EliminationResult:
    candidate_id: str
    variants: tuple[EliminationVariant, ...]
    audits: tuple[VariantAudit, ...]
    survived: tuple[str, ...]
    failed: tuple[str, ...]

    @property
    def delayed_status(self) -> str:
        """Delay is reported, never used as a universal elimination gate."""
        for audit in self.audits:
            if audit.variant == "delayed":
                return "SURVIVED" if audit.selected == self.candidate_id else "FAILED"
        return "NOT_RUN"


def _clip(p: float) -> float:
    return min(0.999999, max(0.000001, p))


def make_variants(predictions: Mapping[str, Sequence[float]], target: str) -> tuple[EliminationVariant, ...]:
    """Generate deterministic semantic stress variants for one candidate."""
    base = {k: tuple(v) for k, v in predictions.items()}
    target_values = base[target]
    inverted = tuple(_clip(1.0 - p) for p in target_values)
    delayed = (target_values[0],) + tuple(target_values[:-1]) if target_values else ()
    attenuated = tuple(_clip(0.5 + 0.55 * (p - 0.5)) for p in target_values)
    return (
        EliminationVariant("inverse", {**base, target: inverted}),
        EliminationVariant("delayed", {**base, target: delayed}),
        EliminationVariant("attenuated", {**base, target: attenuated}),
    )


def eliminate_winner(
    *,
    labels: Sequence[int],
    specs: Sequence[CandidateSpec],
    predictions: Mapping[str, Sequence[float]],
    winner: str,
    max_size: int = 4,
    selector: ModelSelector | None = None,
) -> EliminationResult:
    """Stress a selected candidate and retain complete evidence for every variant.

    Semantic rules:
      * inverse is an intentional kill test and should dislodge the target;
      * attenuated is the robustness gate and must retain the target;
      * delayed is diagnostic only. It is recorded but cannot fail the candidate.
    """
    variants = make_variants(predictions, winner)
    runner = TournamentRunner(selector=selector or ModelSelector(), specs=tuple(specs))
    audits: list[VariantAudit] = []
    survived: list[str] = []
    failed: list[str] = []
    for variant in variants:
        result = runner.run_case(
            TournamentCase(
                name=f"elimination:{variant.name}",
                labels=tuple(labels),
                heldout_predictions=variant.predictions,
                max_size=max_size,
                specs=tuple(specs),
            )
        )
        metrics = tuple(item.metrics for item in result.report.evaluated)
        audits.append(
            VariantAudit(
                variant=variant.name,
                selected=result.decision.selected_model_id,
                status=result.decision.status,
                metrics=metrics,
            )
        )
        if result.decision.selected_model_id == winner:
            survived.append(variant.name)
        else:
            failed.append(variant.name)
    return EliminationResult(winner, variants, tuple(audits), tuple(survived), tuple(failed))
