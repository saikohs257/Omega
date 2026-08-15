from datetime import datetime, timedelta, timezone

import pytest

from experiments.historical_replay import (
    Bar,
    OutcomeSpec,
    assert_no_future_leakage,
    build_causal_observations,
    build_outcome_labels,
    build_replay_rows,
)


def bars(closes):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return [Bar(start + timedelta(hours=i), float(close)) for i, close in enumerate(closes)]


def test_causal_observation_never_uses_future_close():
    data = bars([100, 110, 90])
    before = build_causal_observations(data)
    changed = bars([100, 110, 900])
    after = build_causal_observations(changed)
    assert before[0] == after[0]
    assert before[1] == after[1]


def test_outcome_label_uses_future_only():
    labels = build_outcome_labels(bars([100, 95, 70, 90]), OutcomeSpec(horizon=2, drawdown=0.20))
    assert labels[0].crash is True
    # From the 95 origin, use a non-crash path before the later recovery/crash example.
    labels = build_outcome_labels(bars([100, 95, 85, 90]), OutcomeSpec(horizon=2, drawdown=0.20))
    assert labels[1].crash is False


def test_replay_keeps_outcome_separate_from_observation():
    rows = build_replay_rows(bars([100, 99, 70, 101]), OutcomeSpec(horizon=2, drawdown=0.20))
    assert_no_future_leakage(rows)
    assert not hasattr(rows[0].observation, "crash")
    assert rows[0].outcome.crash is True


def test_csv_loader_rejects_unsorted_and_invalid_prices(tmp_path):
    from experiments.historical_replay import load_bars_csv

    path = tmp_path / "bad.csv"
    path.write_text("timestamp,close\n2020-01-01T01:00:00+00:00,100\n2020-01-01T00:00:00+00:00,90\n")
    with pytest.raises(ValueError, match="strictly increasing"):
        load_bars_csv(path)


def test_outcome_spec_requires_valid_thresholds():
    with pytest.raises(ValueError, match="drawdown"):
        build_outcome_labels(bars([100, 90]), OutcomeSpec(horizon=1, drawdown=1.1))
