from tools.dvqt_relationship_matrix import AMPLITUDES, FEATURES, LAGS, SIGNS, probes, relationship_score


def test_probe_matrix_is_broad():
    ps = probes()
    assert len(ps) > 300
    assert {p.kind for p in ps} == {"pair", "lag", "amplitude", "sign", "phase_condition", "direction", "triple"}


def test_lag_and_sign_sweeps_are_explicit():
    ps = probes()
    assert any(p.kind == "lag" and p.lag == -3 for p in ps)
    assert any(p.kind == "lag" and p.lag == 3 for p in ps)
    assert any(p.kind == "sign" and p.sign == -1 for p in ps)
    assert any(p.kind == "amplitude" and p.amplitude == 4.0 for p in ps)


def test_relationship_gain_definition():
    assert relationship_score(0.50, 0.50) == 0.0
    assert relationship_score(0.50, 0.90) == 0.40
    assert relationship_score(0.90, 0.50) == -0.40
