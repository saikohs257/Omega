from __future__ import annotations

import pytest

from runtime.selection import SelectionThresholds
from tiamat.model_selection import (
    CandidateSpec, ModelMetrics, ModelSelector, binary_auc, brier_score, brier_skill_score, calibration_error,
    consensus, dominates, evaluate_candidate, log_loss, pareto_front,
)


def test_metrics_have_expected_direction() -> None:
    labels = [0, 0, 1, 1]; good = [0.05, 0.10, 0.90, 0.95]; bad = [0.95, 0.90, 0.10, 0.05]
    assert binary_auc(good, labels) == pytest.approx(1.0)
    assert binary_auc(bad, labels) == pytest.approx(0.0)
    assert brier_score(good, labels) < brier_score(bad, labels)
    assert brier_skill_score(good, labels) > 0.0
    assert log_loss(good, labels) < log_loss(bad, labels)


def test_calibration_error_and_evaluation() -> None:
    labels = [0, 0, 1, 1]; probabilities = [0.05, 0.10, 0.90, 0.95]
    metric = evaluate_candidate(CandidateSpec("DQV", ("damage", "charge", "velocity")), probabilities, labels)
    assert calibration_error(probabilities, labels) < 0.10
    assert metric.calibration_error < 0.10
    assert metric.brier < 0.05
    assert metric.brier_skill > 0.80


def test_complexity_penalty() -> None:
    labels = [0, 0, 1, 1]; p = [0.1, 0.2, 0.8, 0.9]
    small = evaluate_candidate(CandidateSpec("DQV", ("damage", "charge", "velocity")), p, labels)
    large = evaluate_candidate(CandidateSpec("ALL", tuple(f"x{i}" for i in range(12))), p, labels)
    assert large.score < small.score


def test_pareto_front_rejects_dominated_candidate() -> None:
    strong = ModelMetrics("strong", 0.90, 0.10, 0.20, 1.0, 3, 100, 0.90, 0.05, 0.60)
    weak = ModelMetrics("weak", 0.85, 0.15, 0.30, 0.9, 5, 100, 0.70, 0.10, 0.40)
    assert [m.model_id for m in pareto_front([strong, weak])] == ["strong"]
    assert dominates(strong, weak)


def test_selector_can_select_best_eligible_candidate() -> None:
    metrics = [
        ModelMetrics("D", 0.82, 0.15, 0.40, 0.95, 1, 100, 0.75, 0.05, 0.40),
        ModelMetrics("DQV", 0.90, 0.08, 0.25, 0.98, 3, 100, 0.88, 0.04, 0.68),
        ModelMetrics("ALL", 0.91, 0.09, 0.26, 0.70, 20, 100, 0.50, 0.08, 0.64),
    ]
    decision = ModelSelector(min_auc=0.80, max_brier=0.20).select(metrics)
    assert decision.status == "SELECTED" and decision.selected_model_id == "DQV"


def test_selector_can_consume_canonical_selection_thresholds() -> None:
    thresholds = SelectionThresholds(brier_skill_min=0.20, auc_min=0.80, ece_max=0.10, version="selection-thresholds-test-v1")
    selector = ModelSelector(selection_thresholds=thresholds, max_brier=0.20)
    assert selector.selection_thresholds is thresholds
    assert selector.min_auc == thresholds.auc_min
    assert selector.min_brier_skill == thresholds.brier_skill_min
    assert selector.max_calibration_error == thresholds.ece_max

    good = ModelMetrics("good", 0.85, 0.15, 0.30, 0.95, 2, 100, 0.80, 0.05, 0.25)
    weak_skill = ModelMetrics("weak", 0.85, 0.15, 0.30, 0.95, 2, 100, 0.80, 0.05, 0.10)
    decision = selector.select([weak_skill, good])
    assert decision.status == "SELECTED" and decision.selected_model_id == "good"


def test_selector_rejects_mixed_canonical_and_legacy_thresholds() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        ModelSelector(selection_thresholds=SelectionThresholds(), min_auc=0.80)


def test_selector_refuses_to_force_a_bad_model() -> None:
    decision = ModelSelector(min_auc=0.60, max_brier=0.25).select([ModelMetrics("bad", 0.52, 0.49, 0.69, 0.40, 4, 50, 0.20, 0.20, 0.0)])
    assert decision.status == "UNRESOLVED" and decision.selected_model_id is None


def test_selector_can_gate_calibration() -> None:
    good = ModelMetrics("good", 0.90, 0.10, 0.20, 0.95, 3, 100, 0.80, 0.05, 0.60)
    overconfident = ModelMetrics("over", 0.95, 0.10, 0.20, 0.95, 2, 100, 0.85, 0.30, 0.60)
    decision = ModelSelector(min_auc=0.80, max_brier=0.20, max_calibration_error=0.10).select([good, overconfident])
    assert decision.selected_model_id == "good"


def test_consensus_surfaces_disagreement() -> None:
    status, mean, models = consensus({"core": 0.90, "path": 0.45, "coupling": 0.80}, tolerance=0.10)
    assert status == "CONTESTED" and mean == pytest.approx((0.90 + 0.45 + 0.80) / 3)
    assert models == ("core", "coupling", "path")


def test_consensus_allows_agreement() -> None:
    status, mean, _ = consensus({"a": 0.80, "b": 0.84, "c": 0.82}, tolerance=0.10)
    assert status == "HIGH" and mean == pytest.approx(0.82)
