"""Twenty synthetic worlds for the TIAMAT adaptive-selection tournament.

The suite is intentionally small and deterministic.  It tests whether the
selector can recover a genuinely informative observable, prefer a useful
combination when no singleton contains the signal, reject deceptive/noisy
observables, and remain unresolved when evidence is insufficient.

These are discovery tests, not claims about the historical TIAMAT corpus.
"""
from __future__ import annotations

from dataclasses import dataclass

from tiamat.model_selection import CandidateSpec
from tiamat.tournament import TournamentCase, TournamentRunner


LABELS = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)
GOOD = tuple(0.10 if y == 0 else 0.90 for y in LABELS)
BAD = tuple(0.90 if y == 0 else 0.10 for y in LABELS)
NEUTRAL = tuple(0.50 for _ in LABELS)
MEDIUM = tuple(0.35 if y == 0 else 0.65 for y in LABELS)


@dataclass(frozen=True)
class World:
    name: str
    signal: str
    combo: tuple[str, ...] | None = None
    unresolved: bool = False


WORLDS = (
    World("damage", "damage"),
    World("recovery", "recovery"),
    World("charge", "charge"),
    World("momentum", "momentum"),
    World("residual_momentum", "residual_momentum"),
    World("residual_load", "residual_load"),
    World("forcing", "forcing"),
    World("flow", "flow"),
    World("initial_velocity", "initial_velocity"),
    World("initial_momentum", "initial_momentum"),
    World("initial_trajectory", "initial_trajectory"),
    World("path", "path"),
    World("trajectory", "trajectory"),
    World("arc", "arc"),
    World("route", "route"),
    World("track", "track"),
    World("orbit", "orbit"),
    World("resistance", "resistance"),
    World("coupling", "coupling"),
    World("interaction_only", "noise", combo=("charge", "coupling")),
)


def _specs(world: World) -> tuple[CandidateSpec, ...]:
    candidates = (
        CandidateSpec("signal", (world.signal,), family="probe"),
        CandidateSpec("noise", ("noise",), family="probe"),
        CandidateSpec("misleading", ("misleading",), family="probe"),
    )
    if world.combo:
        candidates += (CandidateSpec("signal_combo", world.combo, family="probe"),)
    return candidates


def _predictions(world: World) -> dict[str, tuple[float, ...]]:
    predictions = {
        "signal": GOOD if not world.unresolved else NEUTRAL,
        "noise": NEUTRAL,
        "misleading": BAD,
    }
    if world.combo:
        # For the interaction-only world, neither singleton carries the signal.
        predictions["signal"] = NEUTRAL
        predictions["signal_combo"] = GOOD
    return predictions


def test_twenty_worlds_are_explicit_and_cover_the_candidate_vocabulary() -> None:
    assert len(WORLDS) == 20
    assert {w.signal for w in WORLDS} >= {
        "damage", "recovery", "charge", "momentum", "residual_momentum",
        "forcing", "flow", "initial_velocity", "initial_momentum",
        "initial_trajectory", "path", "trajectory", "arc", "route", "track",
        "orbit", "resistance", "coupling",
    }


def test_single_signal_worlds_recover_the_informative_observable() -> None:
    for world in WORLDS[:-1]:
        result = TournamentRunner(specs=_specs(world)).run_case(
            TournamentCase(
                name=world.name,
                labels=LABELS,
                heldout_predictions=_predictions(world),
                max_size=4,
            )
        )
        assert result.decision.status == "SELECTED", world.name
        assert result.best_model_id == "signal", world.name
        assert result.decision.selected_model_id == "signal", world.name


def test_interaction_only_world_prefers_the_combination() -> None:
    world = WORLDS[-1]
    result = TournamentRunner(specs=_specs(world)).run_case(
        TournamentCase(
            name=world.name,
            labels=LABELS,
            heldout_predictions=_predictions(world),
            max_size=4,
        )
    )
    assert result.decision.status == "SELECTED"
    assert result.best_model_id == "signal_combo"
    assert result.decision.selected_model_id == "signal_combo"


def test_weak_world_can_be_explicitly_unresolved() -> None:
    specs = (
        CandidateSpec("a", ("a",)),
        CandidateSpec("b", ("b",)),
        CandidateSpec("c", ("c",)),
    )
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="insufficient_evidence",
            labels=LABELS,
            heldout_predictions={"a": NEUTRAL, "b": NEUTRAL, "c": NEUTRAL},
            max_size=4,
        )
    )
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None
