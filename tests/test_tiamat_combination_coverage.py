"""Coverage tests for exhaustive bounded TIAMAT combination enumeration."""
from __future__ import annotations

from tiamat.combination_search import run_combination_search, staged_combinations
from tiamat.model_selection import CandidateSpec


def test_staged_combinations_is_exhaustive_within_budget() -> None:
    features = ("path", "momentum", "charge", "resistance")
    combos = staged_combinations(features, max_size=3)
    assert len(combos) == 4 + 6 + 4
    assert ("path", "momentum", "charge") in combos
    assert ("momentum", "charge", "resistance") in combos


def test_supplied_combinations_are_all_evaluated_within_budget() -> None:
    labels = (0, 0, 1, 1)
    specs = (
        CandidateSpec("path", ("path",)),
        CandidateSpec("momentum", ("momentum",)),
        CandidateSpec("path_momentum", ("path", "momentum")),
    )
    predictions = {
        "path": (0.20, 0.30, 0.70, 0.80),
        "momentum": (0.30, 0.40, 0.60, 0.70),
        "path_momentum": (0.05, 0.10, 0.90, 0.95),
    }
    report = run_combination_search(specs, predictions, labels, max_size=2)
    assert {r.spec.model_id for r in report.evaluated} == {"path", "momentum", "path_momentum"}
    assert report.rejected == ()


def test_oversized_combination_is_explicitly_rejected_not_silently_dropped() -> None:
    labels = (0, 1, 0, 1)
    spec = CandidateSpec("four_way", ("a", "b", "c", "d"))
    report = run_combination_search(
        (spec,),
        {"four_way": (0.1, 0.9, 0.1, 0.9)},
        labels,
        max_size=3,
    )
    assert report.evaluated == ()
    assert report.rejected == ("four_way",)
