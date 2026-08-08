from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .identification_registry import MODEL_REGISTRY
from .identification_runner import CandidateTrial, IdentificationRunner
from .metric_contract import ProbabilityContract, ProbabilityPredictor, STATE_SPACE, validate_probability_output
from .telemetry import TelemetryRow

@dataclass(frozen=True, slots=True)
class LockedModelEvaluator:
    """Test evaluator that owns exactly one selected model and a mandatory probability contract."""
    model_id: str
    runner: IdentificationRunner
    probability_predictor: ProbabilityPredictor
    probability_contract: ProbabilityContract = ProbabilityContract(STATE_SPACE)

    def __post_init__(self) -> None:
        if self.model_id not in MODEL_REGISTRY:
            raise ValueError(f"unknown locked model: {self.model_id}")
        if self.probability_predictor is None:
            raise ValueError("locked evaluator requires a probability predictor")

    def probability_outputs(self, rows: Sequence[Mapping[str, Any] | TelemetryRow]) -> tuple[Mapping[str, float], ...]:
        normalized = tuple(self.runner.normalize_rows(rows, model_id=self.model_id))
        return tuple(validate_probability_output(row, self.probability_predictor, self.probability_contract) for row in normalized)

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow]) -> CandidateTrial:
        self.probability_outputs(rows)
        report = self.runner.evaluate(rows, model_ids=(self.model_id,))
        if len(report.trials) != 1 or report.trials[0].model_id != self.model_id:
            raise RuntimeError("locked evaluator did not produce exactly one model result")
        return report.trials[0]
