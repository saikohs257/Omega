from __future__ import annotations

from tiamat.model_selection import ModelSelector
from tiamat.tournament import TournamentRunner
from tiamat.world_lab import build_world_lab


def test_world_lab_converts_every_world_to_normal_tournament_cases() -> None:
    cases, expectations = build_world_lab(max_size=4)
    assert len(cases) == len(expectations) == 12
    assert {case.name for case in cases} == {item.world_name for item in expectations}
    for case in cases:
        assert case.labels
        assert case.heldout_predictions


def test_world_lab_tournament_respects_known_and_unknown_worlds() -> None:
    cases, _ = build_world_lab(max_size=4)
    results = TournamentRunner(selector=ModelSelector()).run(cases)
    by_name = {result.case_name: result for result in results}

    assert by_name["clean_state"].decision.status == "SELECTED"
    assert by_name["clean_state"].decision.selected_model_id == "state"

    assert by_name["auc_trap"].decision.status == "UNRESOLVED"
    assert by_name["inverse_signal"].decision.status == "UNRESOLVED"
    assert by_name["regime_conflict"].decision.status == "UNRESOLVED"
    assert by_name["no_signal"].decision.status == "UNRESOLVED"

    assert by_name["calibration_deception"].decision.status == "SELECTED"
    assert by_name["calibration_deception"].decision.selected_model_id == "calibrated"

    assert by_name["interaction_only"].decision.status == "SELECTED"
    assert by_name["interaction_only"].decision.selected_model_id == "A_x_B"

    assert by_name["delayed_trajectory"].decision.selected_model_id == "delayed"
    assert by_name["path_signal"].decision.selected_model_id == "path"
    assert by_name["momentum_signal"].decision.selected_model_id == "initial_momentum"
    assert by_name["resistance_signal"].decision.selected_model_id == "resistance"


def test_world_lab_is_order_invariant() -> None:
    cases, _ = build_world_lab(max_size=4)
    runner = TournamentRunner(selector=ModelSelector())
    forward = {result.case_name: result.decision for result in runner.run(cases)}
    reverse = {result.case_name: result.decision for result in runner.run(tuple(reversed(cases)))}
    assert forward == reverse
