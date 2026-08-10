from __future__ import annotations

from itertools import combinations

from tiamat.combination_search import staged_combinations
from tiamat.model_selection import CandidateSpec


def expand_specs(features: tuple[str, ...], max_size: int) -> tuple[CandidateSpec, ...]:
    return tuple(CandidateSpec("C_" + "__".join(c), c) for c in staged_combinations(features, max_size=max_size))


def test_generation_covers_every_eligible_combination() -> None:
    features = ("path", "trajectory", "momentum", "charge")
    specs = expand_specs(features, 3)
    assert len(specs) == 14
    assert {s.features for s in specs} == {c for n in range(1, 4) for c in combinations(features, n)}


def test_generation_is_deterministic_and_deduplicates_features() -> None:
    first = expand_specs(("path", "momentum", "path", "charge"), 2)
    second = expand_specs(("path", "momentum", "path", "charge"), 2)
    assert first == second
    assert len(first) == 7


def test_budget_never_generates_oversized_models() -> None:
    specs = expand_specs(("a", "b", "c", "d", "e"), 2)
    assert all(1 <= spec.size <= 2 for spec in specs)
