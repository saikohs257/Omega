import pytest

from tiamat.metric_value_report import (
    controlled_scenarios,
    evaluate_scenario,
    metric_disagreement_matrix,
)


def test_controlled_scenarios_cover_event_and_hidden_state_targets() -> None:
    targets = {scenario.target.value for scenario in controlled_scenarios()}
    assert targets == {"event", "hidden_state"}


def test_auc_can_tie_while_probability_metrics_differ() -> None:
    values = evaluate_scenario(controlled_scenarios()[0])
    assert values["auc"] == pytest.approx(1.0)
    assert values["brier"] > 0.0
    assert values["log_loss"] > 0.0


def test_hidden_state_metrics_preserve_probability_information() -> None:
    values = evaluate_scenario(controlled_scenarios()[2])
    assert values["multiclass_brier"] >= 0.0
    assert values["multiclass_log_loss"] >= 0.0
    assert 0.0 <= values["state_accuracy"] <= 1.0


def test_overconfidence_is_penalized_without_changing_top_level_contract() -> None:
    values = evaluate_scenario(controlled_scenarios()[3])
    assert values["multiclass_log_loss"] > 0.0
    assert values["multiclass_brier"] > 0.0


def test_report_is_a_panel_not_a_winner() -> None:
    matrix = metric_disagreement_matrix()
    assert set(matrix) == {
        "perfect_rank_but_poor_calibration",
        "perfectly_calibrated_binary",
        "hidden_state_uncertainty",
        "hidden_state_overconfidence",
    }
