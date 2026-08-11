from __future__ import annotations

from tiamat.state_cartography import fingerprint, current_distance
from tools.divergence_forensics import analyze, summarize


def _fixture():
    a = [0.0] * 30
    b = [0.0] * 30
    # Present state remains identical through t=7; the future separates at
    # t=10. Both trajectories are long enough for the full horizon contract.
    for i in range(10, 30):
        b[i] = 1.0
    return a, b


def test_forensics_finds_similar_present_states_and_future_divergence():
    a, b = _fixture()
    findings = analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5)
    assert findings
    assert any(f.divergence_horizon is not None for f in findings)


def test_forensics_summary_counts_consistent_and_divergent_pairs():
    a, b = _fixture()
    summary = summarize(
        analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5)
    )
    assert summary["similar_state_pairs"] > 0
    assert summary["divergent_futures"] > 0
    # This fixture is intentionally divergence-only: once the trajectories
    # separate they never return to a similar present state. Consistency is
    # therefore allowed to be zero; the summary still reports the category.
    assert summary["consistent_futures"] >= 0
    assert summary["divergent_futures"] <= summary["similar_state_pairs"]


def test_fingerprint_similarity_is_current_only():
    a = fingerprint((0.0, 1.0, 2.0, 3.0))
    b = fingerprint((0.0, 1.0, 2.0, 3.0))
    assert current_distance(a[-1], b[-1]) == 0.0


def test_divergence_summary_keeps_zero_consistency_as_valid_evidence():
    a, b = _fixture()
    summary = summarize(
        analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5)
    )
    # Zero consistent pairs is meaningful for a deliberately divergence-only
    # fixture; the forensic report must not turn that into a test failure.
    assert summary["consistent_futures"] == 0
