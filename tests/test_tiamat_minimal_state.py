from tiamat.minimal_state import run_leave_one_out
from tiamat.model_selection import CandidateSpec

LABELS = (0, 1) * 6
GOOD = tuple(0.1 if y == 0 else 0.9 for y in LABELS)
NEUTRAL = (0.5,) * len(LABELS)


def test_leave_one_out_identifies_essential_and_redundant_features() -> None:
    specs = (
        CandidateSpec("core", ("damage", "momentum"), family="core"),
        CandidateSpec("damage_proxy", ("damage",), family="proxy"),
        CandidateSpec("neutral", ("neutral",), family="probe"),
    )
    result = run_leave_one_out(
        labels=LABELS,
        specs=specs,
        predictions={"core": GOOD, "damage_proxy": GOOD, "neutral": NEUTRAL},
        max_size=2,
    )
    by_feature = {item.feature: item for item in result}
    assert set(by_feature) == {"damage", "momentum", "neutral"}
    assert by_feature["momentum"].classification == "REDUNDANT"
    assert by_feature["damage"].classification == "REDUNDANT"
    assert by_feature["neutral"].classification == "REDUNDANT"
