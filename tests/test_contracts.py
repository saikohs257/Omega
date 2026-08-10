import math

import pytest

from runtime.contracts import (
    ContractViolation,
    OutputContract,
    OutputKind,
    PreflightStatus,
    ProbabilityContract,
)


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


def test_probability_contract_accepts_closed_unit_interval() -> None:
    contract = ProbabilityContract()
    result = contract.preflight((0.0, 0.25, 0.5, 0.75, 1.0))
    assert result.status is PreflightStatus.VALID
    assert result.comparable


def test_probability_contract_rejects_non_probability_outputs() -> None:
    contract = ProbabilityContract()
    with pytest.raises(ContractViolation, match="outside"):
        contract.validate((-0.001, 0.5, 1.001))


def test_probability_contract_rejects_nan_and_infinity() -> None:
    contract = ProbabilityContract()
    for value in (math.nan, math.inf, -math.inf):
        result = contract.preflight((0.5, value))
        assert result.status is PreflightStatus.INCOMPARABLE
        assert not result.comparable


def test_probability_preflight_is_non_fatal_and_partitioned() -> None:
    contract = ProbabilityContract()
    valid = contract.preflight((0.1, 0.9))
    invalid = contract.preflight((0.1, 1.2))

    assert valid.status is PreflightStatus.VALID
    assert invalid.status is PreflightStatus.INCOMPARABLE
    assert invalid.reason
