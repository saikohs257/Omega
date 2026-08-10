from __future__ import annotations

from tiamat.combination_search import run_combination_search, staged_combinations
from tiamat.model_selection import CandidateSpec


def test_staged_combinations_are_bounded_and_deterministic() -> None:
    combos = staged_combinations(("D", "Q", "V"), max_size=2)
    assert combos == (("D",), ("Q",), ("V",), ("D", "Q"), ("D", "V"), ("Q", "V"))


def test_search_keeps_nondominated_candidates() -> None:
    specs = (
        CandidateSpec("D", ("D",)),
        CandidateSpec("DQV", ("D", "Q", "V")),
        CandidateSpec("ALL", ("D", "Q", "V", "R", "F")),
    )
    predictions = {
        "D": (0.2, 0.3, 0.7, 0.8),
        "DQV": (0.1, 0.2, 0.8, 0.9),
        "ALL": (0.1, 0.2, 0.8, 0.9),
    }
    report = run_combination_search(specs, predictions, (0, 0, 1, 1), max_size=3)
    assert {r.spec.model_id for r in report.evaluated} == {"D", "DQV"}
    assert "ALL" in report.rejected
    assert report.best is not None
    assert report.best.spec.model_id == "DQV"
