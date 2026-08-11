from tiamat.state_cartography import StateFingerprint, current_distance, fingerprint, future_distance


def test_fingerprint_tracks_value_velocity_and_acceleration() -> None:
    states = fingerprint((0.0, 1.0, 2.0, 4.0))
    assert len(states) == 4
    assert states[0].value == 0.0
    assert states[1].velocity > 0.0
    assert states[-1].acceleration > 0.0


def test_distance_is_zero_for_identical_state() -> None:
    state = StateFingerprint(0.5, 0.1, -0.02)
    assert current_distance(state, state) == 0.0


def test_future_distance_ignores_current_state_and_compares_future() -> None:
    a = fingerprint((0.0, 1.0, 2.0, 3.0, 4.0))
    b = fingerprint((9.0, 1.0, 2.0, 3.0, 4.0))
    assert current_distance(a[0], b[0]) > 0.0
    assert future_distance(a, b, start=1, horizon=3) == 0.0
