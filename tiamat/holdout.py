from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from .calibration import CalibrationDiagnostic, CalibrationReport
from .experiment_config import DEFAULT_METRIC_WEIGHTS, FeatureDeclaration, TemporalCausalGate, TournamentConfig
from .experiment_manifest import ExperimentManifest, corpus_fingerprint, provenance_fingerprint
from .identification_registry import MODEL_REGISTRY, registry_fingerprint
from .identification_runner import IdentificationRunner, TournamentReport
from .locked_evaluator import LockedModelEvaluator
from .metric_contract import LabelProvenance, MetricContract, ProbabilityContract, ProbabilityPredictor, STATE_SPACE, validate_probability_output
from .telemetry import TelemetryAdapter, TelemetryRow

HOLDOUT_EXPERIMENT_VERSION = "holdout-v3.1"


@dataclass(frozen=True, slots=True)
class HoldoutSplit:
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
            "train": [r.to_mapping() for r in self.train],
            "validation": [r.to_mapping() for r in self.validation],
            "test": [r.to_mapping() for r in self.test],
        }


@dataclass(frozen=True, slots=True)
class HoldoutEvaluation:
    split: HoldoutSplit
    train: TournamentReport
    validation: TournamentReport
    test: Any
    config: TournamentConfig
    gate: TemporalCausalGate
    manifest: ExperimentManifest
    probability_contract: ProbabilityContract
    metric_contract: MetricContract

    @property
    def selected_model_id(self) -> str | None:
        return self.validation.winner.model_id if self.validation.winner else None

    @property
    def locked_model_id(self) -> str | None:
        return self.selected_model_id

    @property
    def test_selected(self):
        return self.test

    @property
    def config_hash(self) -> str:
        return self.config.config_hash()

    @property
    def experiment_id(self) -> str:
        return self.manifest.experiment_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": HOLDOUT_EXPERIMENT_VERSION,
            "experiment_id": self.experiment_id,
            "manifest": self.manifest.to_dict(),
            "config": self.config.to_dict(),
            "causal_gate": self.gate.to_dict(),
            "probability_contract": self.probability_contract.to_dict(),
            "metric_contract": self.metric_contract.to_dict(),
            "locked_model_id": self.locked_model_id,
            "test_selected": None if self.test is None else {"model_id": self.test.model_id, "coverage": self.test.coverage, "transition_error": self.test.transition_error, "score": self.test.score},
            "split": self.split.to_dict(),
        }


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
    probability_contract: ProbabilityContract = field(default_factory=lambda: ProbabilityContract(STATE_SPACE))
    probability_predictor: ProbabilityPredictor | None = None
    label_provenance: LabelProvenance | None = None
    metric_contract: MetricContract | None = None

    def __post_init__(self) -> None:
        fractions = tuple(float(v) for v in (self.train_fraction, self.validation_fraction, self.test_fraction))
        if any(not math.isfinite(v) or v < 0 for v in fractions) or not math.isclose(sum(fractions), 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("holdout fractions must be finite, non-negative and sum to 1.0")
        config = self.config or TournamentConfig(metric_weights=DEFAULT_METRIC_WEIGHTS, split_boundaries=fractions, max_markov_lag=self.gate.max_lookback)
        if config.split_boundaries != fractions:
            raise ValueError("holdout fractions must match config split boundaries")
        if self.gate.max_lookback != config.max_markov_lag:
            object.__setattr__(self, "gate", replace(self.gate, max_lookback=config.max_markov_lag))
        object.__setattr__(self, "config", config)
        if self.label_provenance is None:
            object.__setattr__(self, "label_provenance", LabelProvenance("observed", "mode-v1", "observed controller mode", 1.0, ("mode",), "UNBOUND", 0, False))
        if self.metric_contract is None:
            object.__setattr__(self, "metric_contract", MetricContract(self.probability_contract))
        elif self.metric_contract.probability_contract != self.probability_contract:
            raise ValueError("metric_contract probability contract must match experiment probability contract")

    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]:
        return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)

    def split_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> HoldoutSplit:
        self.gate.validate_rows(rows)
        normalized = self._order_rows(self.normalize_rows(rows, model_id=model_id))
        a, b, c = self._allocate_counts(len(normalized), self.config.split_boundaries)
        return HoldoutSplit(tuple(normalized[:a]), tuple(normalized[a : a + b]), tuple(normalized[a + b : a + b + c]))

    def calibration_report(
        self,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        *,
        controls: Mapping[str, ProbabilityPredictor],
        candidates: Mapping[str, ProbabilityPredictor],
        inference_purity: bool,
        ece_reliability_behavior: str,
        model_id: str = "M3",
    ) -> CalibrationReport:
        """Create calibration diagnostics using predictors only.

        Every control and candidate is normalized, probability-validated, and
        scored through the same MetricContract path. Pre-computed metric bundles
        are intentionally rejected by the type/validation boundary.
        """
        split = self.split_rows(rows, model_id=model_id)
        corpus_hash = corpus_fingerprint([r.to_mapping() for r in (*split.train, *split.validation, *split.test)])
        label = self.label_provenance
        if label is None:
            raise ValueError("label_provenance is required before calibration report generation")
        if label.label_corpus_hash == "UNBOUND":
            label = LabelProvenance(label.label_source, label.label_version, label.label_generation_method, label.label_confidence, label.target_dependencies, corpus_hash, label.label_temporal_offset, label.label_episode_boundary_aware, label.version)
        if label.label_corpus_hash != corpus_hash:
            raise ValueError("label_provenance label_corpus_hash does not match holdout corpus")
        label.validate(max_declared_future_steps=self.config.max_markov_lag)
        label_hash = provenance_fingerprint(label.to_dict())
        metric_hash = provenance_fingerprint(self.metric_contract.to_dict())
        diagnostic = CalibrationDiagnostic(self.metric_contract, self.probability_contract, self.adapter)
        return diagnostic.create_report(
            corpus_manifest_hash=corpus_hash,
            label_provenance_hash=label_hash,
            metric_contract_hash=metric_hash,
            rows=rows,
            controls=controls,
            candidates=candidates,
            inference_purity=inference_purity,
            ece_reliability_behavior=ece_reliability_behavior,
        )

    def _feature_provenance_hash(self, model_id: str) -> str:
        spec = MODEL_REGISTRY[model_id]
        axes = spec.state if isinstance(spec.state, tuple) else ()
        gate = replace(self.gate, features=tuple(FeatureDeclaration(name=axis) for axis in axes))
        gate.validate_features()
        return provenance_fingerprint(gate.to_dict())

    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None, implementation_hash: str | None = None, probability_predictor: ProbabilityPredictor | None = None) -> HoldoutEvaluation:
        predictor = probability_predictor or self.probability_predictor
        if predictor is None:
            raise ValueError("probability_predictor is required before holdout evaluation")
        if self.label_provenance is None:
            raise ValueError("label_provenance is required before holdout evaluation; declare observed, proxy, or model_generated provenance")
        split = self.split_rows(rows)
        ids = tuple(model_ids) if model_ids is not None else None
        train_report = self.runner.evaluate(split.train, model_ids=ids)
        validation_report = self.runner.evaluate(split.validation, model_ids=ids)
        selected = validation_report.winner.model_id if validation_report.winner else None
        if selected is not None:
            for row in tuple(self.runner.normalize_rows(split.test, model_id=selected)):
                validate_probability_output(row, predictor, self.probability_contract)
        locked = None if selected is None else LockedModelEvaluator(selected, self.runner, predictor, self.probability_contract)
        test_result = None if locked is None else locked.evaluate(split.test)
        corpus_hash = corpus_fingerprint([r.to_mapping() for r in (*split.train, *split.validation, *split.test)])
        label = self.label_provenance
        if label.label_corpus_hash != corpus_hash:
            raise ValueError("label_provenance label_corpus_hash does not match holdout corpus")
        label.validate(max_declared_future_steps=self.config.max_markov_lag)
        label_hash = provenance_fingerprint(label.to_dict())
        manifest_model_id = selected or (ids[0] if ids else "M3")
        feature_hash = self._feature_provenance_hash(manifest_model_id)
        probability_hash = provenance_fingerprint(self.probability_contract.to_dict())
        metric_hash = provenance_fingerprint(self.metric_contract.to_dict())
        impl_hash = implementation_hash or self.implementation_hash
        if not impl_hash or impl_hash == "UNBOUND":
            raise ValueError("implementation_hash is required for a reproducible experiment manifest")
        manifest = ExperimentManifest(config_hash=self.config.config_hash(), corpus_hash=corpus_hash, feature_provenance_hash=feature_hash, label_provenance_hash=label_hash, model_registry_hash=registry_fingerprint(), probability_contract_hash=probability_hash, metric_contract_hash=metric_hash, implementation_hash=impl_hash)
        return HoldoutEvaluation(split, train_report, validation_report, test_result, self.config, self.gate, manifest, self.probability_contract, self.metric_contract)

    @staticmethod
    def _order_rows(rows: tuple[TelemetryRow, ...]) -> tuple[TelemetryRow, ...]:
        if any(r.timestamp is None for r in rows):
            return rows
        return tuple(r for _, r in sorted(enumerate(rows), key=lambda p: (p[1].timestamp or "", p[0])))

    @staticmethod
    def _allocate_counts(total: int, fractions: tuple[float, float, float]) -> tuple[int, int, int]:
        raw = [total * f for f in fractions]
        counts = [math.floor(v) for v in raw]
        remainder = total - sum(counts)
        for i in sorted(range(3), key=lambda j: (raw[j] - counts[j], -j), reverse=True)[:remainder]:
            counts[i] += 1
        return tuple(counts)  # type: ignore[return-value]
