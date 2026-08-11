"""Cross-world minimal-state experiment: ablate one feature across multiple worlds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model_selection import CandidateSpec
from .minimal_state import classify_ablation
from .tournament import TournamentCase, TournamentRunner


@dataclass(frozen=True, slots=True)
class World:
    name: str
    labels: tuple[int, ...]
    predictions: Mapping[str, Sequence[float]]


@dataclass(frozen=True, slots=True)
class CrossWorldResult:
    feature: str
    classifications: tuple[tuple[str, str], ...]
    classification: str


def run_cross_world_ablation(
    *,
    worlds: Sequence[World],
    specs: Sequence[CandidateSpec],
    max_size: int = 4,
) -> tuple[CrossWorldResult, ...]:
    features = tuple(dict.fromkeys(f for spec in specs for f in spec.features))
    baseline_specs = tuple(specs)
    baseline_runner = TournamentRunner(specs=baseline_specs)
    results: list[CrossWorldResult] = []
    for feature in features:
        observations: list[tuple[str, str]] = []
        for world in worlds:
            baseline = baseline_runner.run_case(TournamentCase(
                name=f"{world.name}:baseline",
                labels=world.labels,
                heldout_predictions=dict(world.predictions),
                max_size=max_size,
                specs=baseline_specs,
            ))
            ablated_specs = tuple(
                CandidateSpec(spec.model_id, tuple(f for f in spec.features if f != feature), family=spec.family)
                for spec in specs
                if any(f != feature for f in spec.features)
            )
            ablated_predictions = {s.model_id: world.predictions[s.model_id] for s in ablated_specs if s.model_id in world.predictions}
            ablated = TournamentRunner(specs=ablated_specs).run_case(TournamentCase(
                name=f"{world.name}:ablate:{feature}",
                labels=world.labels,
                heldout_predictions=ablated_predictions,
                max_size=max_size,
                specs=ablated_specs,
            ))
            observations.append((world.name, classify_ablation(baseline, ablated)))
        kinds = {kind for _, kind in observations}
        if kinds == {"REDUNDANT"}:
            overall = "REDUNDANT"
        elif kinds == {"ESSENTIAL"}:
            overall = "ESSENTIAL"
        elif "ESSENTIAL" in kinds and "REDUNDANT" in kinds:
            overall = "CONTEXTUAL"
        else:
            overall = "UNRESOLVED"
        results.append(CrossWorldResult(feature, tuple(observations), overall))
    return tuple(results)
