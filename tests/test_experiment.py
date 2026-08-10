import pytest

from runtime.contracts import ContractViolation, OutputContract, OutputKind
from runtime.experiment import ExperimentSpec
from runtime.information_set import InformationSet
from runtime.selection import SelectionThresholds


def make_spec(kind: OutputKind, thresholds: SelectionThresholds | None = None) -> ExperimentSpec:
    return ExperimentSpec(
        hypothesis_id="H1",
        information_set=InformationSet("C1", ("x",), "y", "2026-01-01"),
        metric_contract="metric-v1",
        output_contract=OutputContract.create(kind, "output"),
        implementation_id="impl-1",
        selection_thresholds=thresholds or SelectionThresholds(),
    )


def test_experiment_identity_is_deterministic() -> None:
    assert make_spec(OutputKind.DIAGNOSTIC_SCORE).experiment_id == make_spec(OutputKind.DIAGNOSTIC_SCORE).experiment_id


def test_experiment_identity_changes_with_threshold_values() -> None:
    base = make_spec(OutputKind.PROBABILITY)
    changed = make_spec(OutputKind.PROBABILITY, SelectionThresholds(brier_skill_min=0.06))
    assert base.experiment_id != changed.experiment_id


def test_experiment_identity_changes_with_threshold_semantics() -> None:
    base = make_spec(OutputKind.PROBABILITY)
    changed = make_spec(OutputKind.PROBABILITY, SelectionThresholds(version="selection-thresholds-v2"))
    assert base.experiment_id != changed.experiment_id


def test_probability_preflight_rejects_historical_diagnostic() -> None:
    with pytest.raises(ContractViolation):
        make_spec(OutputKind.DIAGNOSTIC_SCORE).require_probability()


def test_probability_preflight_accepts_probability() -> None:
    make_spec(OutputKind.PROBABILITY).require_probability()
