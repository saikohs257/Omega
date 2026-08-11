from tiamat import ReducedShadow, TiamatMode, blind_replay


def _spine():
    return [
        {"timestamp": "2026-08-10T00:00:00Z", "episode_id": "e1", "B": 0.0, "V": 0.0, "D": 0.0, "tau_mode": 0.0, "mode": "Q"},
        {"timestamp": "2026-08-10T00:01:00Z", "episode_id": "e1", "B": 0.8, "V": 0.2, "D": 0.1, "tau_mode": 1.0, "mode": "P"},
        {"timestamp": "2026-08-10T00:02:00Z", "episode_id": "e1", "B": 0.9, "V": 0.2, "D": 0.2, "tau_mode": 2.0, "mode": "E"},
    ]


def test_reduced_shadow_exposes_only_d_v_q_tau():
    shadow = ReducedShadow()
    state = shadow.from_row(_spine()[0])
    next_state = shadow.step(state, {"D": 0.1, "V": 0.2, "B": 999.0, "Phi": 999.0})
    assert next_state.q is TiamatMode.PRECURSOR
    assert next_state.D == 0.1
    assert next_state.V == 0.2
    assert next_state.tau == 0.0


def test_blind_replay_records_full_reduced_disagreement_without_fitting():
    report = blind_replay(_spine())
    assert report.rows == 3
    assert report.disagreements >= 1
    record = report.records[0]
    assert record.episode_id == "e1"
    assert set(record.reduced_state_snapshot) == {"D", "V", "q", "tau"}
    assert "B" not in record.reduced_state_snapshot
    assert "Phi" not in record.reduced_state_snapshot
