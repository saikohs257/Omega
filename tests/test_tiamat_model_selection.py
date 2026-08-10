from __future__ import annotations

import pytest

from tiamat.model_selection import (
    CandidateSpec,
    ModelMetrics,
    ModelSelector,
    binary_auc,
    brier_score,
    consensus,
    dominates,
    evaluate_candidate,
    log_loss,
    pareto_front,
)


def test_metrics_have_expected_direction() -> None:
    labels = [0, 0, 1, 1]
    good = [0.05, 0.10, 0.90, 0.95]
    bad = [0.95, 0.90, 0.10, 0.05]
    assert binary_auc(good, labels) == pytest.approx(1.0)
    assert binary_auc(bad, labels) == pytest.approx(0.0)
    assert brier_score(good, labels) < brier_score(bad, labels)
    assert log_loss(good, labels) < log_loss(bad, labels)


def test_candidate_evaluation_and_complexity_penalty() -> None:
    labels = [0, 0, 1, 1]
    spec_small = CandidateSpec("DQV", ("damage", "charge", "velocity"))
    spec_large = CandidateSpec("ALL", tuple(f"x{i}" for i in range(12)))
    small = evaluate_candidate(spec_small, [0.1, 0.2, 0.8, 0.9], labels)
    large = evaluate_candidate(spec_large, [0.1, 0.2, 0.8, 0.9], labels)
    assert small.auc == pytest.approx(1.0)
    assert small.brier < 0.05
    assert large.score < small.score


def test_pareto_front_rejects_dominated_candidate() -> None:
    strong = ModelMetrics("strong", 0.90, 0.10, 0.20, 1.0, 3, 100, 0.90)
    weak = ModelMetrics("weak", 0.85, 0.15, 0.30, 0.9, 5, 100, 0.70)
    front = pareto_front([strong, weak])
    assert [m.model_id for m in front] == ["strong"]
    assert dominates(strong, weak)


def test_selector_can_select_best_eligible_candidate() -> None:
    metrics = [
        ModelMetrics("D", 0.82, 0.15, 0.40, 0.95, 1, 100, 0.75),
        ModelMetrics("DQV", 0.90, 0.08, 0.25, 0.98, 3, 100, 0.88),
        ModelMetrics("ALL", 0.91, 0.09, 0.26, 0.70, 20, 100, 0.50),
    ]
    decision = ModelSelector(min_auc=0.80, max_brier=0.20).select(metrics)
    assert decision.status == "SELECTED"
    assert decision.selected_model_id == "DQV"


def test_selector_refuses_to_force_a_bad_model() -> None:
    metrics = [ModelMetrics("bad", 0.52, 0.49, 0.69, 0.40, 4, 50, 0.20)]
    decision = ModelSelector(min_auc=0.60, max_brier=0.25).select(metrics)
    assert decision.status == "UNRESOLVED"
    assert decision.selected_model_id is None


def test_consensus_surfaces_disagreement() -> None:
    status, mean, models = consensus({"core": 0.90, "path": 0.45, "coupling": 0.80}, tolerance=0.10)
    assert status == "CONTESTED"
    assert mean == pytest.approx((0.90 + 0.45 + 0.80) / 3)
    assert models == ("core", "coupling", "path")


def test_consensus_allows_agreement() -> None:
    status, mean, _ = consensus({"a": 0.80, "b": 0.84, "c": 0.82}, tolerance=0.10)
    assert status == "HIGH"
    assert mean == pytest.approx(0.82)
