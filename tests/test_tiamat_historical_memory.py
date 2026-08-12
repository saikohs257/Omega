from tiamat.historical_memory import causal_memory


def test_memory_is_causal_and_freshness_decays_with_run_age():
    rows = [
        {"run_age_h_live": 1, "live_up_pressure_proxy": .2, "LiveDeficit": .8, "SimpleShock": .1, "RecoveryWeakness_v1": .4},
        {"run_age_h_live": 2, "live_up_pressure_proxy": .5, "LiveDeficit": .7, "SimpleShock": .3, "RecoveryWeakness_v1": .5},
    ]
    p = causal_memory(rows, half_life_h=24)
    assert p.age_h == 2
    assert 0 < p.freshness < 1
    assert p.pressure_delta == .3


def test_empty_history_is_neutral():
    p = causal_memory([])
    assert p.age_h == 0
    assert p.freshness == 1
    assert p.pressure_delta == 0


def test_future_row_cannot_change_prior_memory_point():
    prefix = [
        {"run_age_h_live": 1, "live_up_pressure_proxy": .2, "LiveDeficit": .8, "SimpleShock": .1, "RecoveryWeakness_v1": .4},
        {"run_age_h_live": 2, "live_up_pressure_proxy": .5, "LiveDeficit": .7, "SimpleShock": .3, "RecoveryWeakness_v1": .5},
    ]
    before = causal_memory(prefix)
    after = causal_memory(prefix + [
        {"run_age_h_live": 3, "live_up_pressure_proxy": 9.0, "LiveDeficit": 9.0, "SimpleShock": 9.0, "RecoveryWeakness_v1": 9.0}
    ])
    assert before.pressure_delta == .3
    assert after.pressure_delta == 8.5
