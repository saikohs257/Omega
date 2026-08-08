from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from .experiment_config import DEFAULT_METRIC_WEIGHTS, TemporalCausalGate, TournamentConfig
from .experiment_manifest import ExperimentManifest, corpus_fingerprint
from .identification_registry import registry_fingerprint
from .identification_runner import IdentificationRunner, TournamentReport
from .locked_evaluator import LockedModelEvaluator
from .telemetry import TelemetryAdapter, TelemetryRow

HOLDOUT_EXPERIMENT_VERSION = "holdout-v2"

@dataclass(frozen=True, slots=True)
class HoldoutSplit:
    train: tuple[TelemetryRow, ...]
    validation: tuple[TelemetryRow, ...]
    test: tuple[TelemetryRow, ...]
    @property
    def sizes(self) -> dict[str, int]: return {"train": len(self.train), "validation": len(self.validation), "test": len(self.test)}
    def to_dict(self) -> dict[str, Any]: return {"version": HOLDOUT_EXPERIMENT_VERSION, "sizes": self.sizes, "train": [r.to_mapping() for r in self.train], "validation": [r.to_mapping() for r in self.validation], "test": [r.to_mapping() for r in self.test]}

@dataclass(frozen=True, slots=True)
class HoldoutEvaluation:
    split: HoldoutSplit
    train: TournamentReport
    validation: TournamentReport
    test: Any
    config: TournamentConfig
    gate: TemporalCausalGate
    manifest: ExperimentManifest

    @property
    def selected_model_id(self) -> str | None: return self.validation.winner.model_id if self.validation.winner else None
    @property
    def locked_model_id(self) -> str | None: return self.selected_model_id
    @property
    def test_selected(self): return self.test
    @property
    def config_hash(self) -> str: return self.config.config_hash()
    @property
    def experiment_id(self) -> str: return self.manifest.experiment_id
    def to_dict(self) -> dict[str, Any]:
        return {"version": HOLDOUT_EXPERIMENT_VERSION, "experiment_id": self.experiment_id, "manifest": self.manifest.to_dict(), "config": self.config.to_dict(), "causal_gate": self.gate.to_dict(), "locked_model_id": self.locked_model_id, "test_selected": None if self.test is None else {"model_id": self.test.model_id, "coverage": self.test.coverage, "transition_error": self.test.transition_error, "score": self.test.score}, "split": self.split.to_dict()}

@dataclass(frozen=True, slots=True)
class HoldoutExperiment:
    runner: IdentificationRunner = field(default_factory=IdentificationRunner)
    train_fraction: float = 0.6
    validation_fraction: float = 0.2
    test_fraction: float = 0.2
    adapter: TelemetryAdapter = field(default_factory=TelemetryAdapter)
    config: TournamentConfig | None = None
    gate: TemporalCausalGate = field(default_factory=TemporalCausalGate)
    implementation_hash: str = "UNBOUND"

    def __post_init__(self) -> None:
        fractions = tuple(float(v) for v in (self.train_fraction, self.validation_fraction, self.test_fraction))
        if any(not math.isfinite(v) or v < 0 for v in fractions) or not math.isclose(sum(fractions), 1.0, rel_tol=1e-9, abs_tol=1e-9): raise ValueError("holdout fractions must be finite, non-negative and sum to 1.0")
        config = self.config or TournamentConfig(metric_weights=dict(DEFAULT_METRIC_WEIGHTS), split_boundaries=fractions, max_markov_lag=self.gate.max_lookback)
        if config.split_boundaries != fractions: raise ValueError("holdout fractions must match config split boundaries")
        if self.gate.max_lookback != config.max_markov_lag: object.__setattr__(self, "gate", replace(self.gate, max_lookback=config.max_markov_lag))
        object.__setattr__(self, "config", config)

    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]: return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)

    def split_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> HoldoutSplit:
        self.gate.validate_rows(rows)
        normalized = self._order_rows(self.normalize_rows(rows, model_id=model_id))
        a, b, c = self._allocate_counts(len(normalized), self.config.split_boundaries)
        return HoldoutSplit(tuple(normalized[:a]), tuple(normalized[a:a+b]), tuple(normalized[a+b:a+b+c]))

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None, implementation_hash: str | None = None) -> HoldoutEvaluation:
        split = self.split_rows(rows)
        ids = tuple(model_ids) if model_ids is not None else None
        train_report = self.runner.evaluate(split.train, model_ids=ids)
        validation_report = self.runner.evaluate(split.validation, model_ids=ids)
        selected = validation_report.winner.model_id if validation_report.winner else None
        locked = None if selected is None else LockedModelEvaluator(selected, self.runner)
        test_result = None if locked is None else locked.evaluate(split.test)
        corpus_hash = corpus_fingerprint([r.to_mapping() for r in (*split.train, *split.validation, *split.test)])
        manifest = ExperimentManifest(self.config.config_hash(), corpus_hash, registry_fingerprint(), implementation_hash or self.implementation_hash)
        return HoldoutEvaluation(split, train_report, validation_report, test_result, self.config, self.gate, manifest)

    @staticmethod
    def _order_rows(rows: tuple[TelemetryRow, ...]) -> tuple[TelemetryRow, ...]:
        if any(r.timestamp is None for r in rows): return rows
        return tuple(r for _, r in sorted(enumerate(rows), key=lambda p: (p[1].timestamp or "", p[0])))

    @staticmethod
    def _allocate_counts(total: int, fractions: tuple[float, float, float]) -> tuple[int, int, int]:
        raw = [total * f for f in fractions]; counts = [math.floor(v) for v in raw]; remainder = total - sum(counts)
        for i in sorted(range(3), key=lambda j: (raw[j] - counts[j], -j), reverse=True)[:remainder]: counts[i] += 1
        return tuple(counts)  # type: ignore[return-value]
