import pytest

from runtime.contracts import OutputContract, OutputKind
from runtime.experiment import ExperimentSpec
from runtime.experiment_result import ExperimentResult
from runtime.information_set import InformationSet
from runtime.test_spine import TestSpine, TestSpineViolation


def make_result(scope: str) -> ExperimentResult:
    experiment = ExperimentSpec(
        hypothesis_id="H1",
        information_set=InformationSet("C1", ("x",), "y", "2026-01-01"),
        metric_contract="metric-v1",
        output_contract=OutputContract.create(OutputKind.DIAGNOSTIC_SCORE, "diagnostic"),
        implementation_id="impl-1",
    )
    return ExperimentResult.from_experiment(experiment, "manifest-1", scope)


def test_locked_spine_rejects_adaptive_components() -> None:
    spine = TestSpine("holdout-1")
    with pytest.raises(TestSpineViolation):
        spine.read("pond")
    with pytest.raises(TestSpineViolation):
        spine.read("end")


def test_locked_spine_allows_non_adaptive_reader() -> None:
    assert TestSpine("holdout-1").read("court") is None


def test_unlocked_spine_is_not_a_mutation_permission() -> None:
    assert TestSpine("sandbox-1", locked=False).read("pond") is None


def test_spine_accepts_only_explicit_test_results() -> None:
    spine = TestSpine("test-1")
    accepted = spine.accept(make_result("test"))
    assert len(accepted.result_ids) == 1


def test_spine_rejects_validation_result() -> None:
    with pytest.raises(TestSpineViolation):
        TestSpine("test-1").accept(make_result("validation"))


def test_spine_accept_is_idempotent() -> None:
    spine = TestSpine("test-1")
    result = make_result("test")
    accepted = spine.accept(result)
    assert accepted.accept(result) is accepted
