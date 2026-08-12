import pytest

from tiamat.metric_discovery import (
    TargetKind,
    binary_metric_profile,
    hidden_state_metric_profile,
    metric_value_delta,
)


def test_binary_metric_panel_does_not_choose_a_primary_metric() -> None:
    profile = binary_metric_profile([0.1, 0.8, 0.2, 0.9], [0, 1, 0, 1])
    assert profile.target is TargetKind.EVENT
    assert {item.name for item in profile.observations} == {
        "auc", "brier", "log_loss", "calibration_error"
    }
    assert not profile.unresolved
    assert "no primary metric" in profile.reason


def test_hidden_state_profile_uses_probability_aware_metrics() -> None:
    profile = hidden_state_metric_profile(
        [[0.8, 0.15, 0.05], [0.10, 0.80, 0.10], [0.05, 0.15, 0.80]],
        [0, 1, 2],
    )
    assert {item.name for item in profile.observations} == {
        "multiclass_brier", "multiclass_log_loss", "state_accuracy"
    }
    assert profile.by_name["state_accuracy"].value == pytest.approx(1.0)
    assert profile.by_name["multiclass_log_loss"].value < 0.3


def test_metric_delta_respects_direction() -> None:
    profile = binary_metric_profile([0.1, 0.8, 0.2, 0.9], [0, 1, 0, 1])
    brier = profile.by_name["brier"]
    worse = type(brier)(brier.name, brier.value + 0.1, brier.direction, brier.target, brier.interpretation)
    assert metric_value_delta(brier, worse) == pytest.approx(-0.1)


def test_hidden_state_requires_valid_probability_simplex() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        hidden_state_metric_profile([[0.7, 0.7], [0.2, 0.8]], [0, 1])
