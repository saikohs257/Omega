from tools.dvqt_b_fingerprint import B_AMPS, B_LAGS, B_SIGNS, SUBSTITUTES, probes


def test_b_fingerprint_has_temporal_and_perturbation_sweeps():
    ps = probes()
    assert len(ps) >= 40
    assert B_LAGS == tuple(range(-10, 11))
    assert -1.0 in B_SIGNS
    assert 8.0 in B_AMPS
    assert len(SUBSTITUTES) >= 10


def test_b_fingerprint_contains_adversarial_controls():
    kinds = {p.kind for p in probes()}
    assert {"hold", "randomize_within_world", "permute_across_world", "phase_shuffle", "time_reverse"} <= kinds
