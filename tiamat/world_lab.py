"""Deterministic laboratory adapter from adversarial worlds to tournaments.

The laboratory keeps the hidden generating mechanism outside the selector while
converting each synthetic world into a normal held-out TournamentCase. Each world
also carries its explicit candidate vocabulary so the tournament cannot silently
substitute the production candidate library for the blinded laboratory world.
"""
from __future__ import annotations

from dataclasses import dataclass

from .adversarial_worlds import AdversarialWorld, build_adversarial_worlds
from .model_selection import CandidateSpec
from .tournament import TournamentCase


@dataclass(frozen=True, slots=True)
class WorldExpectation:
    world_name: str
    truth_mechanism: str
    candidate_ids: tuple[str, ...]


def world_to_case(world: AdversarialWorld, *, max_size: int = 4) -> tuple[TournamentCase, WorldExpectation]:
    """Hide the world mechanism while preserving its explicit candidate set."""
    specs = tuple(
        CandidateSpec(
            model_id=name,
            features=("A", "B") if name == "A_x_B" else (name,),
        )
        for name in world.predictions
    )
    predictions = {spec.model_id: world.predictions[spec.model_id] for spec in specs}
    case = TournamentCase(
        name=world.name,
        labels=world.labels,
        heldout_predictions=predictions,
        max_size=max_size,
        specs=specs,
    )
    return case, WorldExpectation(world.name, world.truth_mechanism, tuple(spec.model_id for spec in specs))


def build_world_lab(*, max_size: int = 4) -> tuple[tuple[TournamentCase, ...], tuple[WorldExpectation, ...]]:
    """Return all deterministic worlds as ordinary tournament cases."""
    pairs = tuple(world_to_case(world, max_size=max_size) for world in build_adversarial_worlds())
    return tuple(case for case, _ in pairs), tuple(expectation for _, expectation in pairs)
