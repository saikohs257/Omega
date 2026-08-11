"""Adversarial elimination: try to kill tournament winners without changing truth."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model_selection import CandidateSpec, ModelSelector
from .tournament import TournamentCase, TournamentRunner


@dataclass(frozen=True, slots=True)
class EliminationVariant:
    name: str
    predictions: Mapping[str, Sequence[float]]


@dataclass(frozen=True, slots=True)
class EliminationResult:
    candidate_id: str
    variants: tuple[EliminationVariant, ...]
    survived: tuple[str, ...]
    failed: tuple[str, ...]


def _clip(p: float) -> float:
    return min(0.999999, max(0.000001, p))


def make_variants(predictions: Mapping[str, Sequence[float]], target: str) -> tuple[EliminationVariant, ...]:
    """Generate deterministic stress variants for one candidate."""
    base = {k: tuple(v) for k, v in predictions.items()}
    target_values = base[target]
    inverted = tuple(_clip(1.0 - p) for p in target_values)
    delayed = (target_values[0],) + tuple(target_values[:-1]) if target_values else ()
    noisy = tuple(_clip(0.5 + 0.55 * (p - 0.5)) for p in target_values)
    return (
        EliminationVariant("inverse", {**base, target: inverted}),
        EliminationVariant("delayed", {**base, target: delayed}),
        EliminationVariant("attenuated", {**base, target: noisy}),
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
    """Stress a selected candidate and record whether it remains selected."""
    variants = make_variants(predictions, winner)
    runner = TournamentRunner(selector=selector or ModelSelector(), specs=tuple(specs))
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
        if result.decision.selected_model_id == winner:
            survived.append(variant.name)
        else:
            failed.append(variant.name)
    return EliminationResult(winner, variants, tuple(survived), tuple(failed))
