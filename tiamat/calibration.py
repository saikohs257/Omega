from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

from .experiment_manifest import canonical_hash
from .metric_contract import MetricContract, ProbabilityContract, ProbabilityPredictor, validate_probability_output
from .telemetry import TelemetryAdapter, TelemetryRow

CALIBRATION_REPORT_VERSION = "calibration-report-v1"


@dataclass(frozen=True, slots=True)
class ControlMetricSet:
    """Frozen control metrics for a calibration pass."""

    nll: float
    brier: float
    ece: float
    label: str

    def __post_init__(self) -> None:
        for name, value in (("nll", self.nll), ("brier", self.brier), ("ece", self.ece)):
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"control metric {name} must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {"nll": float(self.nll), "brier": float(self.brier), "ece": float(self.ece), "label": self.label}


@dataclass(frozen=True, slots=True)
class CandidateDiagnostic:
    model_id: str
    metrics: dict[str, float]
    rows: int

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("candidate model_id is required")
        if self.rows < 0:
            raise ValueError("candidate rows must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "rows": self.rows, "metrics": {k: float(v) for k, v in sorted(self.metrics.items())}}


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    corpus_manifest_hash: str
    label_provenance_hash: str
    metric_contract_hash: str
    controls: tuple[ControlMetricSet, ...]
    candidates: tuple[CandidateDiagnostic, ...]
    null_floor_check: bool
    spread_check: dict[str, Any]
    ece_reliability_behavior: str
    inference_purity: bool
    decision: str
    decision_rationale: str
    report_version: str = CALIBRATION_REPORT_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("corpus_manifest_hash", self.corpus_manifest_hash),
            ("label_provenance_hash", self.label_provenance_hash),
            ("metric_contract_hash", self.metric_contract_hash),
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{name} must be a 64-character identity hash")
        if self.decision not in {"PROCEED", "HOLD"}:
            raise ValueError("decision must be PROCEED or HOLD")

    @property
    def calibration_hash(self) -> str:
        return canonical_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "corpus_manifest_hash": self.corpus_manifest_hash,
            "label_provenance_hash": self.label_provenance_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "controls": [control.to_dict() for control in self.controls],
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "null_floor_check": self.null_floor_check,
            "spread_check": dict(self.spread_check),
            "ece_reliability_behavior": self.ece_reliability_behavior,
            "inference_purity": self.inference_purity,
            "decision": self.decision,
            "decision_rationale": self.decision_rationale,
            "calibration_hash": self.calibration_hash,
        }


@dataclass(frozen=True, slots=True)
class CalibrationDiagnostic:
    """Inference-only diagnostic stage before selector activation."""

    metric_contract: MetricContract
    probability_contract: ProbabilityContract
    adapter: TelemetryAdapter
    control_labels: tuple[str, ...] = ("uniform", "majority", "historical")
    spread_threshold: float = 0.05

    def evaluate_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, probability_predictor: ProbabilityPredictor, model_id: str = "M3") -> tuple[dict[str, float], int]:
        normalized = tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)
        scored: list[tuple[Mapping[str, float], str]] = []
        for row in normalized:
            probs = validate_probability_output(row, probability_predictor, self.probability_contract)
            target = row.mode.value if hasattr(row.mode, "value") else str(row.mode)
            scored.append((probs, target))
        return self.metric_contract.score(scored), len(normalized)

    def make_report(
        self,
        *,
        corpus_manifest_hash: str,
        label_provenance_hash: str,
        metric_contract_hash: str,
        controls: Mapping[str, Mapping[str, float]],
        candidates: Mapping[str, Mapping[str, float]],
        inference_purity: bool,
        ece_reliability_behavior: str,
    ) -> CalibrationReport:
        control_sets = tuple(
            ControlMetricSet(label=name, nll=float(metrics["nll"]), brier=float(metrics["brier"]), ece=float(metrics["ece"]))
            for name, metrics in sorted(controls.items())
        )
        candidate_sets = tuple(
            CandidateDiagnostic(model_id=model_id, metrics={k: float(v) for k, v in metrics.items()}, rows=int(metrics.get("rows", 0)))
            for model_id, metrics in sorted(candidates.items())
        )
        spread = {
            metric: (max((c.metrics.get(metric, 0.0) for c in candidate_sets), default=0.0) - min((c.metrics.get(metric, 0.0) for c in candidate_sets), default=0.0))
            for metric in ("nll", "brier", "ece")
        }
        null_floor_check = all(control.nll >= 0.0 for control in control_sets)
        proceed = null_floor_check and all(spread[m] >= self.spread_threshold for m in spread)
        return CalibrationReport(
            corpus_manifest_hash=corpus_manifest_hash,
            label_provenance_hash=label_provenance_hash,
            metric_contract_hash=metric_contract_hash,
            controls=control_sets,
            candidates=candidate_sets,
            null_floor_check=null_floor_check,
            spread_check={"threshold": self.spread_threshold, "observed": spread, "pass": proceed},
            ece_reliability_behavior=ece_reliability_behavior,
            inference_purity=inference_purity,
            decision="PROCEED" if proceed and inference_purity else "HOLD",
            decision_rationale=(
                "Calibration diagnostics cleared the null floor and spread threshold"
                if proceed and inference_purity
                else "Calibration diagnostics failed the gating threshold or inference purity check"
            ),
        )
