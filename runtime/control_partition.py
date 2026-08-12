from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from runtime.contracts import PreflightResult, PreflightStatus, ProbabilityContract


@dataclass(frozen=True, slots=True)
class PredictorPreflight:
    predictor_id: str
    result: PreflightResult

    @property
    def comparable(self) -> bool:
        return self.result.status is PreflightStatus.VALID


@dataclass(frozen=True, slots=True)
class ControlsPartition:
    """Non-fatal controls-run partition after probability preflight."""

    valid: tuple[str, ...]
    incomparable: tuple[PredictorPreflight, ...]

    def reason_for(self, predictor_id: str) -> str | None:
        for item in self.incomparable:
            if item.predictor_id == predictor_id:
                return item.result.reason
        return None

    @property
    def valid_count(self) -> int:
        return len(self.valid)

    @property
    def incomparable_count(self) -> int:
        return len(self.incomparable)


def preflight_controls(
    predictions: Mapping[str, Sequence[float]],
    *,
    contract: ProbabilityContract | None = None,
) -> ControlsPartition:
    """Partition predictors without aborting the controls-only run."""
    probability_contract = contract or ProbabilityContract()
    valid: list[str] = []
    incomparable: list[PredictorPreflight] = []
    for predictor_id, values in predictions.items():
        result = probability_contract.preflight(values)
        if result.status is PreflightStatus.VALID:
            valid.append(predictor_id)
        else:
            incomparable.append(PredictorPreflight(predictor_id, result))
    return ControlsPartition(tuple(sorted(valid)), tuple(incomparable))
