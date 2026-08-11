from tiamat.tournament_scorecard import build_scorecard, render_scorecard


def test_tournament_scorecard_is_complete_and_passes() -> None:
    score = build_scorecard()
    assert score.worlds == 12
    assert score.failures == 0
    assert score.selected + score.unresolved == score.worlds
    assert score.winner_counts
    text = render_scorecard(score)
    assert "TIAMAT TOURNAMENT SCORECARD" in text
    assert "failures=0" in text
