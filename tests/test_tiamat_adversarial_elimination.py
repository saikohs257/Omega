from tiamat.adversarial_elimination import eliminate_winner
from tiamat.model_selection import CandidateSpec

LABELS = (0, 1) * 6
GOOD = tuple(0.1 if y == 0 else 0.9 for y in LABELS)
NEUTRAL = (0.5,) * len(LABELS)


def test_winner_elimination_reports_survival_and_failure() -> None:
    specs = (
        CandidateSpec("winner", ("state",)),
        CandidateSpec("neutral", ("neutral",)),
    )
    result = eliminate_winner(
        labels=LABELS,
        specs=specs,
        predictions={"winner": GOOD, "neutral": NEUTRAL},
        winner="winner",
        max_size=1,
    )
    assert result.candidate_id == "winner"
    # Delayed is diagnostic-only and therefore belongs in neither gate set.
    assert set(result.survived) | set(result.failed) == {"inverse", "attenuated"}
    assert set(result.survived).isdisjoint(result.failed)
    assert result.failed
    assert result.delayed_status == "FAILED"
