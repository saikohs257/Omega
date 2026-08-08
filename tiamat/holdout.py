from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from .experiment_config import DEFAULT_METRIC_WEIGHTS, TemporalCausalGate, TournamentConfig
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
    def sizes(self) -> dict[str, int]:
        return {"train": len(self.train), "validation": len(self.validation), "test": len(self.test)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": HOLDOUT_EXPERIMENT_VERSION,
            "sizes": self.sizes,
            "train": [row.to_mapping() for row in self.train],
            "validation": [row.to_mapping() for row in self.validation],
            "test": [row.to_mapping() for row in self.test],
        }


@dataclass(frozen=True, slots=True)
class SplitTournament:
    """Tournament result for a single split."""

    name: str
    report: TournamentReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "winner": None if self.report.winner is None else self.report.winner.model_id,
            "trials": [
                {
                    "model_id": trial.model_id,
                    "role": trial.role,
                    "axes": list(trial.axes),
                    "rows": trial.rows,
                    "supported_rows": trial.supported_rows,
                    "coverage": trial.coverage,
                    "transition_error": trial.transition_error,
                    "complexity": trial.complexity,
                    "is_control": trial.is_control,
                    "score": trial.score,
                }
                for trial in self.report.trials
            ],
        }


@dataclass(frozen=True, slots=True)
class HoldoutEvaluation:
    """Train / validation / test identification report.

    Model selection is based on validation only. The test report is strictly a
    final out-of-sample measurement and can never change the selected model.
    """

    split: HoldoutSplit
    train: TournamentReport
    validation: TournamentReport
    test: TournamentReport
    config: TournamentConfig
    gate: TemporalCausalGate

    @property
    def selected_model_id(self) -> str | None:
        if self.validation.winner is None:
            return None
        return self.validation.winner.model_id

    @property
    def locked_model_id(self) -> str | None:
        return self.selected_model_id

    @property
    def test_selected(self):
        if self.selected_model_id is None:
            return None
        return next((trial for trial in self.test.trials if trial.model_id == self.selected_model_id), None)

    @property
    def config_hash(self) -> str:
        return self.config.config_hash()

    def to_dict(self) -> dict[str, Any]:
        selected = self.test_selected
        return {
            "version": HOLDOUT_EXPERIMENT_VERSION,
            "config_version": self.config.config_version,
            "config_hash": self.config_hash,
            "locked_model_id": self.locked_model_id,
            "selected_model_id": self.selected_model_id,
            "test_selected": None if selected is None else {
                "model_id": selected.model_id,
                "coverage": selected.coverage,
                "transition_error": selected.transition_error,
                "score": selected.score,
            },
            "config": self.config.to_dict(),
            "causal_gate": self.gate.to_dict(),
            "split": self.split.to_dict(),
            "splits": [
                SplitTournament("train", self.train).to_dict(),
                SplitTournament("validation", self.validation).to_dict(),
                SplitTournament("test", self.test).to_dict(),
            ],
        }


@dataclass(frozen=True, slots=True)
class HoldoutExperiment:
    """Deterministic held-out identification experiment for TIAMAT."""

    runner: IdentificationRunner = field(default_factory=IdentificationRunner)
    train_fraction: float = 0.6
    validation_fraction: float = 0.2
    test_fraction: float = 0.2
    adapter: TelemetryAdapter = field(default_factory=TelemetryAdapter)
    config: TournamentConfig | None = None
    gate: TemporalCausalGate = field(default_factory=TemporalCausalGate)

    def __post_init__(self) -> None:
        fractions = (float(self.train_fraction), float(self.validation_fraction), float(self.test_fraction))
        if any(not math.isfinite(value) or value < 0.0 for value in fractions):
            raise ValueError("holdout fractions must be finite and non-negative")
        if not math.isclose(sum(fractions), 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("holdout fractions must sum to 1.0")

        config = self.config
        if config is None:
            config = TournamentConfig(
                metric_weights=dict(DEFAULT_METRIC_WEIGHTS),
                split_boundaries=fractions,
                max_markov_lag=self.gate.max_lookback,
                complexity_definition="axis_count",
                stability_definition="innovation_autocorrelation_plus_parameter_stability",
                random_seed=0,
                telemetry_schema_version="tiamat.telemetry.v1",
            )
        else:
            if any(not math.isclose(float(boundary), float(fraction), rel_tol=1e-9, abs_tol=1e-9) for boundary, fraction in zip(config.split_boundaries, fractions)):
                raise ValueError("holdout fractions must match config split boundaries")
            if self.gate.max_lookback != config.max_markov_lag:
                object.__setattr__(self, "gate", replace(self.gate, max_lookback=config.max_markov_lag))

        object.__setattr__(self, "config", config)

    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]:
        return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)

    def split_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> HoldoutSplit:
        self.gate.validate_rows(rows)
        normalized = self.normalize_rows(rows, model_id=model_id)
        if not normalized:
            return HoldoutSplit((), (), ())
        ordered = self._order_rows(normalized)
        train_count, validation_count, test_count = self._allocate_counts(len(ordered), self.config.split_boundaries)
        train_end = train_count
        validation_end = train_end + validation_count
        return HoldoutSplit(
            train=tuple(ordered[:train_end]),
            validation=tuple(ordered[train_end:validation_end]),
            test=tuple(ordered[validation_end:validation_end + test_count]),
        )

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None) -> HoldoutEvaluation:
        split = self.split_rows(rows)
        train_report = self.runner.evaluate(split.train, model_ids=model_ids)
        validation_report = self.runner.evaluate(split.validation, model_ids=model_ids)
        test_report = self.runner.evaluate(split.test, model_ids=model_ids)
        return HoldoutEvaluation(split=split, train=train_report, validation=validation_report, test=test_report, config=self.config, gate=self.gate)

    @staticmethod
    def _order_rows(rows: tuple[TelemetryRow, ...]) -> tuple[TelemetryRow, ...]:
        indexed = list(enumerate(rows))
        if any(row.timestamp is None for row in rows):
            return rows
        indexed.sort(key=lambda item: (item[1].timestamp or "", item[0]))
        return tuple(row for _, row in indexed)

    @staticmethod
    def _allocate_counts(total: int, fractions: tuple[float, float, float]) -> tuple[int, int, int]:
        raw = [total * fraction for fraction in fractions]
        counts = [math.floor(value) for value in raw]
        remainder = total - sum(counts)
        order = sorted(range(3), key=lambda index: (raw[index] - counts[index], -index), reverse=True)
        for index in order[:remainder]:
            counts[index] += 1
        if total >= 3:
            for index in range(3):
                if counts[index] == 0:
                    donor = max(range(3), key=lambda j: counts[j])
                    if counts[donor] > 1:
                        counts[donor] -= 1
                        counts[index] += 1
        return counts[0], counts[1], counts[2]
