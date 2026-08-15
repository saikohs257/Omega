import pytest

from experiments.historical_replay_eval import PredictionRow, evaluate_binary, first_lead_time


def test_binary_metrics_are_computed_without_model_fitting():
    result = evaluate_binary([
        PredictionRow(0, 0.1, False),
        PredictionRow(1, 0.9, True),
        PredictionRow(2, 0.8, True),
        PredictionRow(3, 0.2, False),
    ])
    assert result.n == 4
    assert result.positives == 2
    assert result.true_positive == 2
    assert result.false_positive == 0
    assert result.false_negative == 0
    assert result.brier < 0.05


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError, match="threshold"):
        evaluate_binary([PredictionRow(0, 0.5, False)], threshold=1.1)


def test_lead_time_is_measured_against_first_event():
    rows = [
        PredictionRow(10, 0.2, False),
        PredictionRow(11, 0.6, False),
        PredictionRow(12, 0.8, True),
    ]
    assert first_lead_time(rows) == 1
