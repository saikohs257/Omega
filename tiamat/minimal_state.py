"""Leave-one-feature-out ablation for minimal sufficient state experiments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model_selection import CandidateSpec
from .tournament import TournamentCase, TournamentRunner


@dataclass(frozen=True, slots=True)
class AblationResult:
    feature: str
    baseline_selected: str | None
    ablated_selected: str | None
    baseline_status: str
    ablated_status: str
    classification: str


def classify_ablation(baseline, ablated) -> str:
    """Classify whether removing one feature changes the observed decision."""
    b = baseline.decision
    a = ablated.decision
    if b.status != a.status or b.selected_model_id != a.selected_model_id:
        return "ESSENTIAL"
    return "REDUNDANT"


def _case(name, labels, predictions, max_size, specs):
    return TournamentCase(
        name=name,
        labels=tuple(labels),
        heldout_predictions=predictions,
        max_size=max_size,
        specs=tuple(specs),
    )


def run_leave_one_out(
    *,
    labels: Sequence[int],
    specs: Sequence[CandidateSpec],
    predictions: Mapping[str, Sequence[float]],
    max_size: int = 4,
) -> tuple[AblationResult, ...]:
    """Compare the full candidate library against versions with one feature removed."""
    features = tuple(dict.fromkeys(f for spec in specs for f in spec.features))
    baseline_specs = tuple(specs)
    baseline = TournamentRunner(specs=baseline_specs).run_case(
        _case("baseline", labels, dict(predictions), max_size, baseline_specs)
    )
    results: list[AblationResult] = []
    for feature in features:
        ablated_specs = tuple(
            CandidateSpec(
                spec.model_id,
                tuple(f for f in spec.features if f != feature),
                family=spec.family,
            )
            for spec in specs
            if any(f != feature for f in spec.features)
        )
        ablated_predictions = {
            spec.model_id: predictions[spec.model_id]
            for spec in ablated_specs
            if spec.model_id in predictions
        }
        ablated = TournamentRunner(specs=ablated_specs).run_case(
            _case(
                f"ablate:{feature}",
                labels,
                ablated_predictions,
                max_size,
                ablated_specs,
            )
        )
        results.append(
            AblationResult(
                feature,
                baseline.decision.selected_model_id,
                ablated.decision.selected_model_id,
                baseline.decision.status,
                ablated.decision.status,
                classify_ablation(baseline, ablated),
            )
        )
    return tuple(results)
