import pytest

from runtime.contracts import ContractViolation, OutputContract, OutputKind
from runtime.experiment import ExperimentSpec
from runtime.information_set import InformationSet


def make_spec(kind: OutputKind) -> ExperimentSpec:
    return ExperimentSpec(
        hypothesis_id="H1",
        information_set=InformationSet("C1", ("x",), "y", "2026-01-01"),
        metric_contract="metric-v1",
        output_contract=OutputContract.create(kind, "output"),
        implementation_id="impl-1",
    )


def test_experiment_identity_is_deterministic() -> None:
    assert make_spec(OutputKind.DIAGNOSTIC_SCORE).experiment_id == make_spec(OutputKind.DIAGNOSTIC_SCORE).experiment_id


def test_probability_preflight_rejects_historical_diagnostic() -> None:
    with pytest.raises(ContractViolation):
        make_spec(OutputKind.DIAGNOSTIC_SCORE).require_probability()


def test_probability_preflight_accepts_probability() -> None:
    make_spec(OutputKind.PROBABILITY).require_probability()
