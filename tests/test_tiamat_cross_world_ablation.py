from tiamat.cross_world_ablation import World, run_cross_world_ablation
from tiamat.model_selection import CandidateSpec

LABELS = (0, 1) * 6
GOOD = tuple(0.1 if y == 0 else 0.9 for y in LABELS)
NEUTRAL = (0.5,) * len(LABELS)


def test_cross_world_ablation_can_find_contextual_features() -> None:
    specs = (
        CandidateSpec("core", ("damage", "momentum"), family="core"),
        CandidateSpec("damage_proxy", ("damage",), family="proxy"),
        CandidateSpec("neutral", ("neutral",), family="probe"),
    )
    worlds = (
        World("clean", LABELS, {"core": GOOD, "damage_proxy": GOOD, "neutral": NEUTRAL}),
        World("probe", LABELS, {"core": GOOD, "damage_proxy": NEUTRAL, "neutral": GOOD}),
    )
    result = run_cross_world_ablation(worlds=worlds, specs=specs, max_size=2)
    by_feature = {item.feature: item for item in result}
    assert set(by_feature) == {"damage", "momentum", "neutral"}
    assert by_feature["damage"].classification == "CONTEXTUAL"
