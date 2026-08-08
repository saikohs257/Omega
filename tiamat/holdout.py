from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Real
from typing import Any, Mapping, Sequence

from .identification_runner import IdentificationRunner, TournamentReport
from .telemetry import TelemetryAdapter, TelemetryRow

HOLDOUT_EXPERIMENT_VERSION = "holdout-v1"

@dataclass(frozen=True, slots=True)
class HoldoutSplit:
    """Deterministic temporal split for held-out TIAMAT identification."""
    train: tuple[TelemetryRow, ...]
    validation: tuple[TelemetryRow, ...]
    test: tuple[TelemetryRow, ...]
    @property
    def sizes(self) -> dict[str, int]: return {"train": len(self.train), "validation": len(self.validation), "test": len(self.test)}
    def to_dict(self) -> dict[str, Any]: return {"version": HOLDOUT_EXPERIMENT_VERSION, "sizes": self.sizes, "train": [row.to_mapping() for row in self.train], "validation": [row.to_mapping() for row in self.validation], "test": [row.to_mapping() for row in self.test]}

@dataclass(frozen=True, slots=True)
class SplitTournament:
    name: str
    report: TournamentReport
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "winner": None if self.report.winner is None else self.report.winner.model_id, "trials": [{"model_id": t.model_id, "role": t.role, "axes": list(t.axes), "rows": t.rows, "supported_rows": t.supported_rows, "coverage": t.coverage, "transition_error": t.transition_error, "complexity": t.complexity, "is_control": t.is_control, "score": t.score} for t in self.report.trials]}

@dataclass(frozen=True, slots=True)
class HoldoutEvaluation:
    split: HoldoutSplit
    train: TournamentReport
    validation: TournamentReport
    test: TournamentReport
    @property
    def selected_model_id(self) -> str | None:
        if self.validation.winner is not None: return self.validation.winner.model_id
        if self.train.winner is not None: return self.train.winner.model_id
        return None
    @property
    def test_selected(self):
        if self.selected_model_id is None: return None
        return next((trial for trial in self.test.trials if trial.model_id == self.selected_model_id), None)
    def to_dict(self) -> dict[str, Any]:
        selected = self.test_selected
        return {"version": HOLDOUT_EXPERIMENT_VERSION, "selected_model_id": self.selected_model_id, "test_selected": None if selected is None else {"model_id": selected.model_id, "coverage": selected.coverage, "transition_error": selected.transition_error, "score": selected.score}, "split": self.split.to_dict(), "splits": [SplitTournament("train", self.train).to_dict(), SplitTournament("validation", self.validation).to_dict(), SplitTournament("test", self.test).to_dict()]}

@dataclass(frozen=True, slots=True)
class HoldoutExperiment:
    runner: IdentificationRunner = field(default_factory=IdentificationRunner)
    train_fraction: float = 0.6
    validation_fraction: float = 0.2
    test_fraction: float = 0.2
    adapter: TelemetryAdapter = field(default_factory=TelemetryAdapter)
    def __post_init__(self) -> None:
        fractions = (("train_fraction", self.train_fraction), ("validation_fraction", self.validation_fraction), ("test_fraction", self.test_fraction))
        for name, value in fractions:
            if isinstance(value, bool) or not isinstance(value, Real): raise TypeError(f"{name} must be a real number, not {type(value).__name__}")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0: raise ValueError(f"{name} must be finite and non-negative")
        total = sum(float(value) for _, value in fractions)
        if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9): raise ValueError("holdout fractions must sum to 1.0")
    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]: return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)
    def split_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> HoldoutSplit:
        normalized = self.normalize_rows(rows, model_id=model_id)
        if not normalized: return HoldoutSplit((), (), ())
        ordered = self._order_rows(normalized)
        a, b, c = self._allocate_counts(len(ordered), (self.train_fraction, self.validation_fraction, self.test_fraction))
        return HoldoutSplit(tuple(ordered[:a]), tuple(ordered[a:a+b]), tuple(ordered[a+b:a+b+c]))
    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None) -> HoldoutEvaluation:
        split = self.split_rows(rows)
        return HoldoutEvaluation(split=split, train=self.runner.evaluate(split.train, model_ids=model_ids), validation=self.runner.evaluate(split.validation, model_ids=model_ids), test=self.runner.evaluate(split.test, model_ids=model_ids))
    @staticmethod
    def _order_rows(rows: tuple[TelemetryRow, ...]) -> tuple[TelemetryRow, ...]:
        indexed = list(enumerate(rows))
        if any(row.timestamp is None for row in rows): return rows
        indexed.sort(key=lambda item: (item[1].timestamp or "", item[0]))
        return tuple(row for _, row in indexed)
    @staticmethod
    def _allocate_counts(total: int, fractions: tuple[float, float, float]) -> tuple[int, int, int]:
        raw = [total * fraction for fraction in fractions]; counts = [math.floor(value) for value in raw]; remainder = total - sum(counts)
        order = sorted(range(3), key=lambda index: (raw[index] - counts[index], -index), reverse=True)
        for index in order[:remainder]: counts[index] += 1
        if total >= 3:
            for index in range(3):
                if counts[index] == 0:
                    donor = max(range(3), key=lambda j: counts[j])
                    if counts[donor] > 1: counts[donor] -= 1; counts[index] += 1
        return counts[0], counts[1], counts[2]
