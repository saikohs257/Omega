from __future__ import annotations

import pytest

from tiamat.adversarial_worlds import build_adversarial_worlds
from tiamat.model_selection import CandidateSpec, ModelSelector
from tiamat.tournament import TournamentCase, TournamentRunner


def _run(world_name: str, *, max_size: int = 3):
    world = next(w for w in build_adversarial_worlds() if w.name == world_name)
    specs = tuple(
        CandidateSpec(
            model_id=name,
            features=tuple(name.split("_x_")) if "_x_" in name else (name,),
            family="adversarial",
        )
        for name in world.predictions
    )
    return world, TournamentRunner(specs=specs, selector=ModelSelector()).run_case(
        TournamentCase(
            name=world.name,
            labels=world.labels,
            heldout_predictions=world.predictions,
            max_size=max_size,
        )
    )


def test_world_catalog_is_broad_and_deterministic() -> None:
    first = build_adversarial_worlds()
    second = build_adversarial_worlds()
    assert first == second
    assert len(first) >= 10
    assert {w.name for w in first} >= {
        "clean_state",
        "auc_trap",
        "interaction_only",
        "delayed_trajectory",
        "no_signal",
        "path_signal",
        "momentum_signal",
        "resistance_signal",
    }


def test_clean_signal_is_selected() -> None:
    world, result = _run("clean_state")
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "state"
    assert result.best_model_id == "state"
    assert world.truth_mechanism == "state"


def test_near_random_perfect_rank_is_rejected_by_skill_gate() -> None:
    _, result = _run("auc_trap")
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None


def test_inverse_signal_is_not_promoted() -> None:
    _, result = _run("inverse_signal")
    assert result.decision.status == "UNRESOLVED"


def test_calibrated_candidate_beats_auc_trap() -> None:
    _, result = _run("calibration_deception")
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "calibrated"


def test_interaction_only_world_discovers_joint_candidate() -> None:
    _, result = _run("interaction_only", max_size=2)
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "A_x_B"


def test_delayed_signal_beats_instantaneous_proxy() -> None:
    _, result = _run("delayed_trajectory")
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "delayed"


def test_regime_conflict_remains_unresolved() -> None:
    _, result = _run("regime_conflict")
    assert result.decision.status == "UNRESOLVED"


def test_no_signal_world_is_unresolved() -> None:
    _, result = _run("no_signal")
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.reason == "no candidate passed minimum evidence gates"


def test_redundant_observables_have_deterministic_tie_break() -> None:
    _, result = _run("redundant_signal")
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "state"


@pytest.mark.parametrize(
    (world_name, expected),
    (
        ("path_signal", "path"),
        ("momentum_signal", "initial_momentum"),
        ("resistance_signal", "resistance"),
    ),
)
def test_physical_language_families_are_discoverable(world_name: str, expected: str) -> None:
    _, result = _run(world_name)
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == expected


def test_candidate_order_does_not_change_selection() -> None:
    world = next(w for w in build_adversarial_worlds() if w.name == "calibration_deception")
    specs_a = tuple(CandidateSpec(name, (name,), family="adversarial") for name in world.predictions)
    specs_b = tuple(reversed(specs_a))
    case = TournamentCase(world.name, world.labels, world.predictions, max_size=1)
    a = TournamentRunner(specs=specs_a).run_case(case)
    b = TournamentRunner(specs=specs_b).run_case(case)
    assert a.decision == b.decision
