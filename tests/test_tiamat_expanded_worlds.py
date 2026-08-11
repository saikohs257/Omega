from __future__ import annotations

from math import log

from tiamat.expanded_worlds import build_expanded_worlds
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
        assert ranked
        # Selector has no access to world.truth; verify it returns capability matches.
        assert all(item.matched_mechanisms for item in ranked)
        assert ranked == tuple(sorted(ranked, key=lambda item: (-item.compatibility, item.component)))


def test_proximity_family_surfaces_proximity_candidate() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "proximity_linear")
    names = [item.component for item in rank_candidates(world.mechanisms)]
    assert "proximity" in names


def test_coupling_family_surfaces_coupling_candidate() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "coupled_threshold")
    names = [item.component for item in rank_candidates(world.mechanisms)]
    assert "coupling" in names


def test_unknown_world_has_no_declared_truth_and_still_runs() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "unknown_world")
    assert world.truth is None
    assert _brier(world.labels, world.predictions["A"]) == 0.25
