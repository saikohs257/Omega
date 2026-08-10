from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity
from runtime.experiment import ExperimentSpec


class ResultBoundaryViolation(ValueError):
    """Raised when a result is not bound to its declared experiment."""


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    experiment_id: str
    manifest_id: str
    scope: str
    metrics: tuple[tuple[str, Any], ...] = ()
    output: Any = None
    result_id: str = ""

    def __post_init__(self) -> None:
        if self.scope not in {"development", "validation", "holdout", "test"}:
            raise ValueError("scope must be development, validation, holdout, or test")
        payload: Mapping[str, Any] = {
            "experiment_id": self.experiment_id,
            "manifest_id": self.manifest_id,
            "scope": self.scope,
            "metrics": tuple(sorted(self.metrics)),
            "output": self.output,
        }
        object.__setattr__(self, "result_id", Identity.calculate(payload).digest)

    @classmethod
    def from_experiment(
        cls,
        experiment: ExperimentSpec,
        manifest_id: str,
        scope: str,
        metrics: Mapping[str, Any] | None = None,
        output: Any = None,
    ) -> "ExperimentResult":
        return cls(
            experiment_id=experiment.experiment_id,
            manifest_id=manifest_id,
            scope=scope,
            metrics=tuple(sorted((metrics or {}).items())),
            output=output,
        )

    def assert_bound_to(self, experiment: ExperimentSpec) -> None:
        if self.experiment_id != experiment.experiment_id:
            raise ResultBoundaryViolation("result is bound to a different experiment")

    def assert_test_eligible(self) -> None:
        if self.scope != "test":
            raise ResultBoundaryViolation("only an explicitly test-scoped result may enter the test spine")
