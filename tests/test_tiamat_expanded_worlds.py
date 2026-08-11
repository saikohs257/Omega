from __future__ import annotations

from tiamat.expanded_worlds import build_expanded_worlds
from tiamat.expanded_world_selector_eval import aggregate, evaluate_world
from tiamat.world_selector import rank_candidates


def _brier(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    return sum((float(a) - b) ** 2 for a, b in zip(y, p)) / len(y)


def test_expanded_world_catalog_is_broad_and_deterministic() -> None:
    first = build_expanded_worlds()
    second = build_expanded_worlds()
    assert first == second
    assert len(first) >= 20
    names = {world.name for world in first}
    assert {"proximity_linear", "accelerating", "phase_reversal", "coupled_threshold", "unknown_world"} <= names


def test_selector_is_mechanism_conditioned_not_truth_conditioned() -> None:
    worlds = build_expanded_worlds()
    for world in worlds:
        ranked = rank_candidates(world.mechanisms)
        if "unknown" in world.mechanisms:
            assert ranked == ()
            continue
        assert ranked
        assert all(item.matched_mechanisms for item in ranked)
        assert ranked == tuple(sorted(ranked, key=lambda item: (-item.compatibility, item.component)))


def test_selector_evaluation_has_explicit_abstention_and_topk_metrics() -> None:
    worlds = build_expanded_worlds()
    stats = aggregate(worlds, k=3)
    assert stats["worlds"] >= 20
    assert stats["known_worlds"] >= 19
    assert stats["unknown_worlds"] == 1
    assert stats["unknown_abstention_rate"] == 1.0
    assert 0.0 <= stats["top1_hit_rate"] <= 1.0
    assert 0.0 <= stats["topk_hit_rate"] <= 1.0
    assert stats["topk_hit_rate"] >= stats["top1_hit_rate"]


def test_proximity_family_surfaces_proximity_candidate() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "proximity_linear")
    names = [item.component for item in rank_candidates(world.mechanisms)]
    assert "proximity" in names


def test_coupling_family_surfaces_coupling_candidate() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "coupled_threshold")
    names = [item.component for item in rank_candidates(world.mechanisms)]
    assert "coupling" in names


def test_unknown_world_is_first_class_abstention() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "unknown_world")
    assert world.truth is None
    assert _brier(world.labels, world.predictions["A"]) == 0.25
    result = evaluate_world(world)
    assert result["known"] is False
    assert result["abstained"] is True
    assert result["top1"] is None
    assert result["topk"] == ()


def test_reversal_world_surfaces_phase_in_candidate_set() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "reversal_after_acceleration")
    result = evaluate_world(world, k=3)
    assert "phase" in result["topk"]
    assert result["topk_hit"] is True
