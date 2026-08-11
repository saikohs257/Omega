from tiamat.tournament_round3 import CANDIDATE_ORDER, audit_segments, run_round_three, render


def test_round_three_is_deterministic_and_ranked() -> None:
    first = run_round_three()
    second = run_round_three()
    assert first == second
    assert len(first.survivors) >= 1
    assert all(len(match.a) > 0 and len(match.b) > 0 for match in first.matches)
    assert all(match.a != match.b for match in first.matches)
    assert all(match.unresolved == 0 for match in first.matches)
    assert first.ranking == tuple(sorted(first.ranking, key=lambda item: (-item[1], item[0])))
    text = render(first)
    assert "TIAMAT TOURNAMENT ROUND 3 — COMMON HELD-OUT PANEL" in text
    assert "panel_n=" in text
    assert "brier=" in text
    assert "log_loss=" in text
    assert "auc=" in text
    assert "calibration_error=" in text
    assert "brier_skill=" in text
    assert "SEGMENT METRICS" in text


def test_round_three_has_full_segment_metric_matrix() -> None:
    rows = audit_segments()
    survivors = tuple(name for name in CANDIDATE_ORDER if any(row.candidate == name for row in rows))
    segments = tuple(dict.fromkeys(row.segment for row in rows))
    assert len(segments) == len(CANDIDATE_ORDER)
    assert survivors
    assert len(rows) == len(segments) * len(survivors)
    assert all(row.brier >= 0.0 for row in rows)
    assert all(row.log_loss >= 0.0 for row in rows)
    assert all(0.0 <= row.auc <= 1.0 for row in rows)
