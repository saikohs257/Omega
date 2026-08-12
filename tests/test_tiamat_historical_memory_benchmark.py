from tiamat.historical_memory_benchmark import compare_instantaneous_and_memory


def _rows():
    return [
        {"run_age_h_live": 1, "live_up_pressure_proxy": 0.2, "LiveDeficit": 0.8, "SimpleShock": 0.1, "RecoveryWeakness_v1": 0.4},
        {"run_age_h_live": 2, "live_up_pressure_proxy": 0.5, "LiveDeficit": 0.7, "SimpleShock": 0.3, "RecoveryWeakness_v1": 0.5},
        {"run_age_h_live": 3, "live_up_pressure_proxy": 0.4, "LiveDeficit": 0.6, "SimpleShock": 0.2, "RecoveryWeakness_v1": 0.6},
    ]


def test_memory_benchmark_is_timestamp_aligned():
    comparisons = compare_instantaneous_and_memory(_rows(), half_life_h=24)
    assert {item.name for item in comparisons} == {
        "live_up_pressure_proxy", "LiveDeficit", "SimpleShock", "RecoveryWeakness_v1",
        "freshness", "pressure_ema", "deficit_ema", "shock_ema", "recovery_ema",
        "pressure_delta", "run_age_h_live",
    }
    assert all(item.n == 3 for item in comparisons)


def test_memory_benchmark_does_not_inspect_targets():
    rows = _rows()
    rows[0]["target"] = 1
    rows[1]["target"] = 0
    rows[2]["target"] = 1
    with_targets = compare_instantaneous_and_memory(rows)
    rows_without_targets = _rows()
    without_targets = compare_instantaneous_and_memory(rows_without_targets)
    assert with_targets == without_targets


def test_memory_benchmark_rejects_empty_input():
    try:
        compare_instantaneous_and_memory([])
    except ValueError as exc:
        assert "replay row" in str(exc)
    else:
        raise AssertionError("empty input should fail")
