from __future__ import annotations

from statistics import mean

from tiamat.state_cartography import fingerprint, current_distance
from tools.divergence_forensics import analyze, summarize


def _future(values, start, horizon):
    end = min(start + horizon + 1, len(values))
    if end <= start + 1:
        return 0.0
    return mean(abs(values[i] - values[i]) for i in range(start + 1, end))


def test_forensics_finds_similar_present_states_and_future_divergence():
    a = [0.0] * 8 + [0.0, 0.0, 0.0, 0.0]
    b = [0.0] * 8 + [0.0, 0.0, 1.0, 1.0]
    findings = analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5)
    assert findings
    assert any(f.divergence_horizon is not None for f in findings)


def test_forensics_summary_counts_consistent_and_divergent_pairs():
    a = [0.0] * 8 + [0.0, 0.0, 0.0, 0.0]
    b = [0.0] * 8 + [0.0, 0.0, 1.0, 1.0]
    summary = summarize(analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5))
    assert summary["similar_state_pairs"] > 0
    assert summary["divergent_futures"] > 0


def test_fingerprint_similarity_is_current_only():
    a = fingerprint((0.0, 1.0, 2.0, 3.0))
    b = fingerprint((0.0, 1.0, 2.0, 3.0))
    assert current_distance(a[-1], b[-1]) == 0.0
