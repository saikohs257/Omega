from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .identification_registry import MODEL_REGISTRY
from .identification_runner import CandidateTrial, IdentificationRunner
from .metric_contract import ProbabilityContract, ProbabilityPredictor, validate_probability_output
from .telemetry import TelemetryAdapter, TelemetryRow


@dataclass(frozen=True, slots=True)
class LockedModelEvaluator:
    """Test evaluator that owns exactly one selected model and enforces its probability contract."""
    model_id: str
    runner: IdentificationRunner
    probability_predictor: ProbabilityPredictor
    probability_contract: ProbabilityContract

    def __post_init__(self) -> None:
        if self.model_id not in MODEL_REGISTRY:
            raise ValueError(f"unknown locked model: {self.model_id}")

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow]) -> CandidateTrial:
        adapter = self.runner.adapter if hasattr(self.runner, "adapter") else TelemetryAdapter()
        normalized = tuple(adapter.normalize(row, model_id=self.model_id) for row in rows)
        for row in normalized:
            validate_probability_output(row, self.probability_predictor, self.probability_contract)
        report = self.runner.evaluate(normalized, model_ids=(self.model_id,))
        if len(report.trials) != 1 or report.trials[0].model_id != self.model_id:
            raise RuntimeError("locked evaluator did not produce exactly one model result")
        return report.trials[0]
