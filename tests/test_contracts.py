import pytest

from runtime.contracts import ContractViolation, OutputContract, OutputKind


def test_diagnostic_score_is_not_probability() -> None:
    contract = OutputContract.create(OutputKind.DIAGNOSTIC_SCORE, "tiamat.hazard_score")
    assert not contract.is_probability()
    with pytest.raises(ContractViolation):
        contract.require_probability()


def test_probability_contract_is_explicit() -> None:
    contract = OutputContract.create(OutputKind.PROBABILITY, "predictor.event_probability")
    assert contract.is_probability()
    contract.require_probability()


def test_contract_metadata_is_canonicalized() -> None:
    left = OutputContract.create(OutputKind.RISK_SCORE, "risk", {"b": 2, "a": 1})
    right = OutputContract.create(OutputKind.RISK_SCORE, "risk", {"a": 1, "b": 2})
    assert left == right
