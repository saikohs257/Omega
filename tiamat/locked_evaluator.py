from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .identification_registry import MODEL_REGISTRY
from .identification_runner import CandidateTrial, IdentificationRunner
from .telemetry import TelemetryAdapter, TelemetryRow

@dataclass(frozen=True, slots=True)
class LockedModelEvaluator:
    """Test evaluator that structurally owns exactly one already-selected model."""
    model_id: str
    runner: IdentificationRunner

    def __post_init__(self) -> None:
        if self.model_id not in MODEL_REGISTRY:
            raise ValueError(f"unknown locked model: {self.model_id}")

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow]) -> CandidateTrial:
        report = self.runner.evaluate(rows, model_ids=(self.model_id,))
        if len(report.trials) != 1 or report.trials[0].model_id != self.model_id:
            raise RuntimeError("locked evaluator did not produce exactly one model result")
        return report.trials[0]
