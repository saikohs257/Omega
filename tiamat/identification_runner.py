from __future__ import annotations

from dataclasses import dataclass, field
import math
from statistics import fmean
from typing import Any, Callable, Mapping, Sequence

from .identification_registry import MODEL_REGISTRY, ModelSpec
from .state import TiamatState
from .telemetry import CANONICAL_CONTROL_AXES, TelemetryAdapter, TelemetryRow, axes_for_model
from .transition import transition

TransitionFn = Callable[[TiamatState, Mapping[str, Any]], TiamatState]


@dataclass(frozen=True, slots=True)
class CandidateTrial:
    """Summary of how well a candidate model is supported by a telemetry row set."""

    model_id: str
    role: str
    axes: tuple[str, ...]
    rows: int
    supported_rows: int
    coverage: float
    transition_error: float | None
    complexity: int
    is_control: bool = False

    @property
    def score(self) -> float:
        penalty = self.transition_error if self.transition_error is not None else 0.0
        return self.coverage - penalty - 0.01 * self.complexity


@dataclass(frozen=True, slots=True)
class TournamentReport:
    """Ordered identification outcomes for one telemetry corpus."""

    trials: tuple[CandidateTrial, ...]

    @property
    def winner(self) -> CandidateTrial | None:
        return self.trials[0] if self.trials else None


@dataclass(frozen=True, slots=True)
class IdentificationRunner:
    """Deterministic runner for M0–M7 state-sufficiency experiments.

    The runner is intentionally neutral: it scores how well a candidate model is
    supported by the telemetry and how consistently it replays through the
    current transition surface. It does not declare a model canonical.
    """

    adapter: TelemetryAdapter = field(default_factory=TelemetryAdapter)
    transition_fn: TransitionFn = transition
    control_model_id: str = "M7"
    control_axes: tuple[str, ...] = CANONICAL_CONTROL_AXES

    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]:
        return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)

    def axes_for(self, model_id: str) -> tuple[str, ...]:
        if model_id == self.control_model_id:
            return self.control_axes
        return axes_for_model(model_id)

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None) -> TournamentReport:
        normalized = self.normalize_rows(rows)
        ids = tuple(model_ids or MODEL_REGISTRY.keys())
        trials = tuple(sorted((self._evaluate_model(normalized, model_id) for model_id in ids), key=self._trial_order))
        return TournamentReport(trials=trials)

    def build_frames(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], model_id: str) -> tuple[dict[str, Any], ...]:
        return self.adapter.frame(rows, model_id)

    def build_states(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], model_id: str = "M3") -> tuple[TiamatState, ...]:
        return self.adapter.states(rows, model_id)

    def _evaluate_model(self, rows: tuple[TelemetryRow, ...], model_id: str) -> CandidateTrial:
        axes = self.axes_for(model_id)
        supported = tuple(row for row in rows if row.supports(model_id, control_axes=self.control_axes))
        coverage = (len(supported) / len(rows)) if rows else 0.0
        transition_error = self._transition_error(rows, axes) if len(rows) > 1 else None
        spec = MODEL_REGISTRY.get(model_id)
        role = spec.role if spec is not None else "candidate"
        return CandidateTrial(
            model_id=model_id,
            role=role,
            axes=axes,
            rows=len(rows),
            supported_rows=len(supported),
            coverage=coverage,
            transition_error=transition_error,
            complexity=len(axes),
            is_control=(model_id == self.control_model_id),
        )

    def _transition_error(self, rows: tuple[TelemetryRow, ...], axes: tuple[str, ...]) -> float:
        if not rows:
            return 0.0
        errors: list[float] = []
        for before, after in zip(rows, rows[1:]):
            predicted = self.transition_fn(before.to_state(), after.to_mapping())
            observed = after.to_state()
            errors.append(self._state_error(predicted, observed, axes))
        return fmean(errors) if errors else 0.0

    def _state_error(self, predicted: TiamatState, observed: TiamatState, axes: tuple[str, ...]) -> float:
        if not axes:
            return 0.0
        errors: list[float] = []
        for axis in axes:
            predicted_value = getattr(predicted, axis, None)
            observed_value = getattr(observed, axis, None)
            if predicted_value is None or observed_value is None:
                errors.append(1.0)
                continue
            if axis in {"B", "D"}:
                errors.append(min(1.0, abs(float(predicted_value) - float(observed_value))))
            elif axis in {"tau_D", "tau_mode"}:
                observed_float = float(observed_value)
                scale = max(1.0, abs(observed_float))
                errors.append(min(1.0, abs(float(predicted_value) - observed_float) / scale))
            elif axis in {"V", "Phi"}:
                predicted_float = float(predicted_value)
                observed_float = float(observed_value)
                if not math.isfinite(predicted_float) or not math.isfinite(observed_float):
                    errors.append(1.0)
                else:
                    errors.append(min(1.0, abs(predicted_float - observed_float)))
            else:
                errors.append(0.0 if predicted_value == observed_value else 1.0)
        return fmean(errors) if errors else 0.0

    @staticmethod
    def _trial_order(trial: CandidateTrial) -> tuple[float, float, int, str]:
        return (
            trial.transition_error if trial.transition_error is not None else 1.0,
            -trial.coverage,
            trial.complexity,
            trial.model_id,
        )
