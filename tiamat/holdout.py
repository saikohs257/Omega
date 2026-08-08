from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from .experiment_config import DEFAULT_METRIC_WEIGHTS, FeatureDeclaration, TemporalCausalGate, TournamentConfig
from .experiment_manifest import ExperimentManifest, corpus_fingerprint, provenance_fingerprint
from .identification_registry import MODEL_REGISTRY, registry_fingerprint
from .identification_runner import IdentificationRunner, TournamentReport
from .locked_evaluator import LockedModelEvaluator
from .metric_contract import LabelProvenance, ProbabilityContract
from .telemetry import TelemetryAdapter, TelemetryRow

HOLDOUT_EXPERIMENT_VERSION = "holdout-v3"


@dataclass(frozen=True, slots=True)
class HoldoutSplit:
    train: tuple[TelemetryRow, ...]
    validation: tuple[TelemetryRow, ...]
    test: tuple[TelemetryRow, ...]

    @property
    def sizes(self) -> dict[str, int]:
        return {"train": len(self.train), "validation": len(self.validation), "test": len(self.test)}

    def to_dict(self) -> dict[str, Any]:
        return {"version": HOLDOUT_EXPERIMENT_VERSION, "sizes": self.sizes, "train": [r.to_mapping() for r in self.train], "validation": [r.to_mapping() for r in self.validation], "test": [r.to_mapping() for r in self.test]}


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
    probability_contract: ProbabilityContract = field(default_factory=lambda: ProbabilityContract(("Q", "P", "E", "C", "H", "R", "Rf")))
    label_provenance: LabelProvenance | None = None

    def __post_init__(self) -> None:
        fractions = tuple(float(v) for v in (self.train_fraction, self.validation_fraction, self.test_fraction))
        if any(not math.isfinite(v) or v < 0 for v in fractions) or not math.isclose(sum(fractions), 1.0, rel_tol=1e-9, abs_tol=1e-9): raise ValueError("holdout fractions must be finite, non-negative and sum to 1.0")
        config = self.config or TournamentConfig(metric_weights=DEFAULT_METRIC_WEIGHTS, split_boundaries=fractions, max_markov_lag=self.gate.max_lookback)
        if config.split_boundaries != fractions: raise ValueError("holdout fractions must match config split boundaries")
        if self.gate.max_lookback != config.max_markov_lag: object.__setattr__(self, "gate", replace(self.gate, max_lookback=config.max_markov_lag))
        object.__setattr__(self, "config", config)
        if self.label_provenance is None:
            object.__setattr__(self, "label_provenance", LabelProvenance("observed", "mode-v1", "observed controller mode", 1.0, ("mode",), "UNBOUND", 0, False))

    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]:
        return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)

    def split_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> HoldoutSplit:
        self.gate.validate_rows(rows)
        normalized = self._order_rows(self.normalize_rows(rows, model_id=model_id))
        a, b, c = self._allocate_counts(len(normalized), self.config.split_boundaries)
        return HoldoutSplit(tuple(normalized[:a]), tuple(normalized[a:a+b]), tuple(normalized[a+b:a+b+c]))

    def _feature_provenance_hash(self, model_id: str) -> str:
        spec = MODEL_REGISTRY[model_id]
        axes = spec.state if isinstance(spec.state, tuple) else ()
        features = tuple(FeatureDeclaration(name=axis) for axis in axes)
        gate = replace(self.gate, features=features)
        gate.validate_features()
        return provenance_fingerprint(gate.to_dict())

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None, implementation_hash: str | None = None) -> HoldoutEvaluation:
        split = self.split_rows(rows)
        ids = tuple(model_ids) if model_ids is not None else None
        train_report = self.runner.evaluate(split.train, model_ids=ids)
        validation_report = self.runner.evaluate(split.validation, model_ids=ids)
        selected = validation_report.winner.model_id if validation_report.winner else None
        locked = None if selected is None else LockedModelEvaluator(selected, self.runner)
        test_result = None if locked is None else locked.evaluate(split.test)
        corpus_hash = corpus_fingerprint([r.to_mapping() for r in (*split.train, *split.validation, *split.test)])
        manifest_model_id = selected or (ids[0] if ids else "M3")
        label = self.label_provenance
        if label.label_corpus_hash == "UNBOUND":
            label = LabelProvenance(label.label_source, label.label_version, label.label_generation_method, label.label_confidence, label.label_feature_dependencies, corpus_hash, label.label_temporal_offset, label.label_episode_boundary_aware, label.version)
        label.validate(max_declared_future_steps=self.config.max_markov_lag)
        label_hash = provenance_fingerprint(label.to_dict())
        feature_hash = self._feature_provenance_hash(manifest_model_id)
        probability_hash = provenance_fingerprint(self.probability_contract.to_dict())
        impl_hash = implementation_hash or self.implementation_hash
        if not impl_hash or impl_hash == "UNBOUND": raise ValueError("implementation_hash is required for a reproducible experiment manifest")
        manifest = ExperimentManifest(config_hash=self.config.config_hash(), corpus_hash=corpus_hash, feature_provenance_hash=feature_hash, label_provenance_hash=label_hash, model_registry_hash=registry_fingerprint(), probability_contract_hash=probability_hash, implementation_hash=impl_hash)
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
