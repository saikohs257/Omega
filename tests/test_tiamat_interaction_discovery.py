import numpy as np

from tiamat.interaction_discovery import discover_interactions


def _xor_world(n=400, seed=17):
    rng = np.random.default_rng(seed)
    a = rng.random(n)
    b = rng.random(n)
    y = ((a > 0.5) ^ (b > 0.5)).astype(int)
    signals = {
        "probe_01": a,
        "probe_02": b,
        "noise_01": rng.random(n),
        "noise_02": rng.normal(size=n),
    }
    return signals, y


def test_blind_detector_discovers_relationship_without_named_ab():
    signals, y = _xor_world()
    results = discover_interactions(signals, y, shuffle_trials=12)
    promoted = {(r.left, r.right) for r in results if r.promoted}
    assert ("probe_01", "probe_02") in promoted


def test_marginals_are_not_the_source_of_xor_discovery():
    signals, y = _xor_world()
    results = discover_interactions(signals, y, shuffle_trials=12)
    pair = next(r for r in results if {r.left, r.right} == {"probe_01", "probe_02"})
    assert pair.individual_auc_left < 0.60
    assert pair.individual_auc_right < 0.60
    assert pair.joint_auc > 0.95
    assert pair.synergy > 0.35


def test_shuffle_control_breaks_the_discovered_relationship():
    signals, y = _xor_world()
    results = discover_interactions(signals, y, shuffle_trials=20)
    pair = next(r for r in results if {r.left, r.right} == {"probe_01", "probe_02"})
    assert pair.shuffle_gap > 0.35
    assert pair.promoted


def test_independent_strong_signals_do_not_get_promoted_as_interaction():
    rng = np.random.default_rng(31)
    n = 400
    a = rng.random(n)
    b = rng.random(n)
    y = (a > 0.5).astype(int)
    signals = {"strong": a, "independent": b, "noise": rng.random(n)}
    results = discover_interactions(signals, y, shuffle_trials=12)
    pair = next(r for r in results if {r.left, r.right} == {"strong", "independent"})
    assert pair.synergy < 0.10
    assert not pair.promoted
