from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from runtime.control_partition import ControlsPartition, preflight_controls
from runtime.contracts import ProbabilityContract


@dataclass(frozen=True, slots=True)
class ControlsRun:
    """Preflighted controls-only input partition.

    Only predictors in ``partition.valid`` may be passed to downstream scoring.
    Contract violations remain recorded as incomparable rather than aborting the
    enclosing controls run.
    """

    partition: ControlsPartition
    predictions: Mapping[str, Sequence[float]]

    @property
    def comparable_predictions(self) -> dict[str, Sequence[float]]:
        return {predictor_id: self.predictions[predictor_id] for predictor_id in self.partition.valid}

    @property
    def incomparable_predictions(self) -> tuple[str, ...]:
        return tuple(item.predictor_id for item in self.partition.incomparable)


def prepare_controls_run(
    predictions: Mapping[str, Sequence[float]],
    *,
    contract: ProbabilityContract | None = None,
) -> ControlsRun:
    """Prepare a controls-only run and isolate contract-invalid predictors."""
    partition = preflight_controls(predictions, contract=contract)
    return ControlsRun(partition=partition, predictions=predictions)
