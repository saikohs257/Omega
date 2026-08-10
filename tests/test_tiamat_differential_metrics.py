from __future__ import annotations

import math

import pytest

from tiamat.model_selection import (
    CandidateSpec,
    brier_score,
    brier_skill_score,
    calibration_error,
    consensus,
    dominates,
    evaluate_candidate,
    pareto_front,
)

LABELS = tuple(i % 2 for i in range(20))
PERFECT = tuple(0.9 if y else 0.1 for y in LABELS)
WEAK = tuple(0.51 if y else 0.49 for y in LABELS)
INVERSE = tuple(0.9 if not y else 0.1 for y in LABELS)


def test_chain_01_perfect_signal_has_positive_skill() -> None:
    assert brier_score(PERFECT, LABELS) < brier_score(WEAK, LABELS)
    assert brier_skill_score(PERFECT, LABELS) > brier_skill_score(WEAK, LABELS)


def test_chain_02_inverse_signal_has_negative_skill() -> None:
    assert brier_skill_score(INVERSE, LABELS) < 0.0


def test_chain_03_calibration_is_a_distinct_axis_from_ranking() -> None:
    perfect_ece = calibration_error(PERFECT, LABELS)
    weak_ece = calibration_error(WEAK, LABELS)
    assert perfect_ece != weak_ece
    assert weak_ece < perfect_ece


def test_chain_04_pareto_front_keeps_non_dominated_tradeoffs() -> None:
    strong = evaluate_candidate(CandidateSpec("strong", ("state",)), PERFECT, LABELS)
    weak = evaluate_candidate(CandidateSpec("weak", ("proxy",)), WEAK, LABELS)
    inverse = evaluate_candidate(CandidateSpec("inverse", ("wrong",)), INVERSE, LABELS)
    front = {metric.model_id for metric in pareto_front((strong, weak, inverse))}
    assert "strong" in front
    assert "weak" in front
    assert "inverse" not in front


def test_chain_05_dominance_is_directionally_consistent() -> None:
    strong = evaluate_candidate(CandidateSpec("strong", ("state",)), PERFECT, LABELS)
    inverse = evaluate_candidate(CandidateSpec("inverse", ("wrong",)), INVERSE, LABELS)
    assert dominates(strong, inverse)
    assert not dominates(inverse, strong)


def test_chain_06_consensus_exposes_disagreement_instead_of_forcing_a_vote() -> None:
    status, mean, members = consensus({"path": 0.90, "momentum": 0.20}, tolerance=0.10)
    assert status == "CONTESTED"
    assert mean == 0.55
    assert members == ("momentum", "path")


def test_chain_07_probability_contract_rejects_out_of_range_values() -> None:
    with pytest.raises(ValueError, match=r"probabilities must be finite and in \[0, 1\]"):
        brier_score((0.2, 1.1), (0, 1))


def test_chain_08_probability_contract_rejects_nonfinite_values() -> None:
    with pytest.raises(ValueError, match=r"probabilities must be finite and in \[0, 1\]"):
        brier_score((0.2, math.nan), (0, 1))


def test_chain_09_label_contract_rejects_nonbinary_values() -> None:
    with pytest.raises(ValueError, match="labels must be binary"):
        brier_score((0.2, 0.8), (0, 2))


def test_chain_10_calibration_bins_must_be_positive() -> None:
    with pytest.raises(ValueError, match="bins must be positive"):
        calibration_error(PERFECT, LABELS, bins=0)


def test_chain_11_consensus_tolerance_is_boundary_stable() -> None:
    status, mean, members = consensus({"a": 0.40, "b": 0.50}, tolerance=0.10)
    assert status == "HIGH"
    assert mean == 0.45
    assert members == ("a", "b")


def test_chain_12_candidate_order_does_not_change_pareto_front() -> None:
    strong = evaluate_candidate(CandidateSpec("strong", ("state",)), PERFECT, LABELS)
    weak = evaluate_candidate(CandidateSpec("weak", ("proxy",)), WEAK, LABELS)
    front_a = tuple(m.model_id for m in pareto_front((strong, weak)))
    front_b = tuple(m.model_id for m in pareto_front((weak, strong)))
    assert front_a == front_b
