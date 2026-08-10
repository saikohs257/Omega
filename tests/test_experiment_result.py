from __future__ import annotations

import pytest

from runtime.contracts import OutputContract, OutputKind
from runtime.experiment import ExperimentSpec
from runtime.experiment_result import ExperimentResult, ResultBoundaryViolation
from runtime.information_set import InformationSet


def make_experiment(implementation_id: str = "impl-1") -> ExperimentSpec:
    return ExperimentSpec(
        hypothesis_id="H1",
        information_set=InformationSet("C1", ("x",), "y", "2026-01-01"),
        metric_contract="metric-v1",
        output_contract=OutputContract.create(OutputKind.DIAGNOSTIC_SCORE, "diagnostic"),
        implementation_id=implementation_id,
    )


def test_result_is_bound_to_exact_experiment() -> None:
    experiment = make_experiment()
    result = ExperimentResult.from_experiment(
        experiment, "manifest-1", "validation", {"score": 0.5}, {"diagnostic": 0.5}
    )
    result.assert_bound_to(experiment)


def test_result_rejects_different_experiment() -> None:
    result = ExperimentResult.from_experiment(make_experiment(), "manifest-1", "validation")
    with pytest.raises(ResultBoundaryViolation):
        result.assert_bound_to(make_experiment("different-implementation"))


def test_non_test_result_cannot_enter_test_spine() -> None:
    result = ExperimentResult.from_experiment(make_experiment(), "manifest-1", "validation")
    with pytest.raises(ResultBoundaryViolation):
        result.assert_test_eligible()


def test_only_explicit_test_scope_is_test_eligible() -> None:
    result = ExperimentResult.from_experiment(make_experiment(), "manifest-1", "test")
    result.assert_test_eligible()


def test_result_identity_changes_when_scope_changes() -> None:
    experiment = make_experiment()
    validation = ExperimentResult.from_experiment(experiment, "manifest-1", "validation")
    holdout = ExperimentResult.from_experiment(experiment, "manifest-1", "holdout")
    assert validation.result_id != holdout.result_id
