from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json
import os
import tempfile
import uuid

from .experiment_manifest import canonical_hash
from .metric_contract import (
    MetricContract,
    ProbabilityContract,
    ProbabilityPredictor,
    validate_probability_output,
)
from .telemetry import TelemetryAdapter, TelemetryRow

CALIBRATION_REPORT_VERSION = "calibration-report-v1.2"
CALIBRATION_ARTIFACT_SCHEMA_VERSION = 2


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ControlMetricSet:
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
    comparable: bool = True
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("candidate model_id is required")
        if self.rows < 0:
            raise ValueError("candidate rows must be non-negative")
        if not self.comparable and not self.reason:
            raise ValueError("incomparable candidate requires a reason")
        for name, value in self.metrics.items():
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"candidate metric {name} must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": self.rows,
            "metrics": {k: float(v) for k, v in sorted(self.metrics.items())},
            "comparable": self.comparable,
            "reason": self.reason,
        }


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
    reliability_bins: tuple[dict[str, Any], ...] = ()
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
        if not self.report_version:
            raise ValueError("report_version is required")

    def canonical_payload(self) -> dict[str, Any]:
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
            "reliability_bins": [dict(bucket) for bucket in self.reliability_bins],
        }

    @property
    def calibration_hash(self) -> str:
        return canonical_hash(self.canonical_payload())

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload() | {"calibration_hash": self.calibration_hash}


@dataclass(frozen=True, slots=True)
class CalibrationDiagnostic:
    """Single scoring path for controls and candidates; no pre-scored input is accepted."""

    metric_contract: MetricContract
    probability_contract: ProbabilityContract
    adapter: TelemetryAdapter
    control_labels: tuple[str, ...] = ("uniform", "majority", "historical")
    spread_threshold: float = 0.05

    def __post_init__(self) -> None:
        if not isfinite(float(self.spread_threshold)) or self.spread_threshold < 0.0:
            raise ValueError("spread_threshold must be finite and non-negative")

    def evaluate_rows(
        self,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        *,
        probability_predictor: ProbabilityPredictor,
        model_id: str,
    ) -> tuple[dict[str, float], int, tuple[dict[str, Any], ...]]:
        normalized = tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)
        scored: list[tuple[Mapping[str, float], str]] = []
        for row in normalized:
            probs = validate_probability_output(row, probability_predictor, self.probability_contract)
            target = row.mode.value if hasattr(row.mode, "value") else str(row.mode)
            scored.append((probs, target))
        metrics = self.metric_contract.score(scored)
        bins = self._reliability_bins(scored)
        return metrics, len(normalized), bins

    def _reliability_bins(self, scored: Sequence[tuple[Mapping[str, float], str]]) -> tuple[dict[str, Any], ...]:
        n_bins = self.metric_contract.ece_bins
        buckets: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]
        states = self.probability_contract.state_space
        for probabilities, target in scored:
            if self.metric_contract.ece_confidence == "true_state_probability":
                confidence = float(probabilities[target])
            else:
                confidence = max(float(probabilities[state]) for state in states)
            prediction = max(states, key=lambda state: float(probabilities[state]))
            index = min(n_bins - 1, int(confidence * n_bins))
            buckets[index].append((confidence, prediction == target))
        result: list[dict[str, Any]] = []
        for index, bucket in enumerate(buckets):
            lower = index / n_bins
            upper = (index + 1) / n_bins
            if bucket:
                mean_confidence = sum(c for c, _ in bucket) / len(bucket)
                empirical_accuracy = sum(1.0 if correct else 0.0 for _, correct in bucket) / len(bucket)
            else:
                mean_confidence = None
                empirical_accuracy = None
            result.append({
                "index": index,
                "edge_lo": lower,
                "edge_hi": upper,
                "center": (lower + upper) / 2.0,
                "mean_confidence": mean_confidence,
                "empirical_accuracy": empirical_accuracy,
                "count": len(bucket),
            })
        if len(result) != n_bins:
            raise AssertionError("reliability writer must emit every configured bin")
        return tuple(result)

    def create_report(
        self,
        *,
        corpus_manifest_hash: str,
        label_provenance_hash: str,
        metric_contract_hash: str,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        controls: Mapping[str, ProbabilityPredictor],
        candidates: Mapping[str, ProbabilityPredictor],
        inference_purity: bool,
        ece_reliability_behavior: str,
        incomparable: Mapping[str, str] | None = None,
    ) -> CalibrationReport:
        if not controls and not candidates and not incomparable:
            raise ValueError("at least one control or candidate predictor is required")
        if not isinstance(ece_reliability_behavior, str) or not ece_reliability_behavior.strip():
            raise ValueError("ece_reliability_behavior must be a non-empty assessment")
        incomparable = dict(incomparable or {})
        control_sets: list[ControlMetricSet] = []
        reliability_by_control: dict[str, tuple[dict[str, Any], ...] | None] = {}
        for name, predictor in sorted(controls.items()):
            metrics, _, bins = self.evaluate_rows(rows, probability_predictor=predictor, model_id=name)
            control_sets.append(ControlMetricSet(label=name, nll=metrics["nll"], brier=metrics["brier"], ece=metrics["ece"]))
            reliability_by_control[name] = bins
        candidate_sets: list[CandidateDiagnostic] = []
        candidate_bins: dict[str, tuple[dict[str, Any], ...] | None] = {}
        for model_id, predictor in sorted(candidates.items()):
            metrics, count, bins = self.evaluate_rows(rows, probability_predictor=predictor, model_id=model_id)
            candidate_sets.append(CandidateDiagnostic(model_id=model_id, metrics=metrics, rows=count))
            candidate_bins[model_id] = bins
        for model_id, reason in sorted(incomparable.items()):
            candidate_sets.append(CandidateDiagnostic(model_id=model_id, metrics={}, rows=0, comparable=False, reason=reason))
            candidate_bins[model_id] = None
        candidates_tuple = tuple(candidate_sets)
        comparable_candidates = tuple(c for c in candidates_tuple if c.comparable)
        state_count = len(self.probability_contract.state_space)
        null_nll_floor = log(state_count)
        candidate_nlls = [c.metrics["nll"] for c in comparable_candidates]
        null_floor_check = bool(candidate_nlls) and all(nll < null_nll_floor for nll in candidate_nlls)
        spread = {
            metric: (
                max((c.metrics.get(metric, 0.0) for c in comparable_candidates), default=0.0)
                - min((c.metrics.get(metric, 0.0) for c in comparable_candidates), default=0.0)
            )
            for metric in ("nll", "brier", "ece")
        }
        spread_pass = len(comparable_candidates) >= 2 and all(spread[m] >= self.spread_threshold for m in spread)
        proceed = null_floor_check and spread_pass
        all_bins: list[dict[str, Any]] = []
        for name, bins in sorted({**reliability_by_control, **candidate_bins}.items()):
            all_bins.append({"predictor": name, "comparable": bins is not None, "reason": incomparable.get(name), "bins": list(bins) if bins is not None else None})
        return CalibrationReport(
            corpus_manifest_hash=corpus_manifest_hash,
            label_provenance_hash=label_provenance_hash,
            metric_contract_hash=metric_contract_hash,
            controls=tuple(control_sets),
            candidates=candidates_tuple,
            null_floor_check=null_floor_check,
            spread_check={"threshold": self.spread_threshold, "null_nll_floor": null_nll_floor, "observed": spread, "candidate_count": len(comparable_candidates), "pass": spread_pass},
            ece_reliability_behavior=ece_reliability_behavior,
            inference_purity=inference_purity,
            decision="PROCEED" if proceed and inference_purity else "HOLD",
            decision_rationale=("Calibration diagnostics cleared the null floor and spread threshold" if proceed and inference_purity else "Calibration diagnostics failed the null-floor, spread, or inference-purity gate"),
            reliability_bins=tuple(all_bins),
        )


class CalibrationBundleWriter:
    """Atomically seals a calibration bundle after hashing every artifact."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)

    @staticmethod
    def _bundle_hash(artifact_hashes: Mapping[str, str]) -> str:
        ordered = [(key, artifact_hashes[key]) for key in sorted(artifact_hashes)]
        return _sha256_bytes(_canonical_json(ordered))

    def write(self, report: CalibrationReport, *, run_id: str) -> Path:
        if not run_id or Path(run_id).name != run_id:
            raise ValueError("run_id must be a simple non-empty path component")
        corpus_hash = report.corpus_manifest_hash
        final_dir = self.root / corpus_hash / run_id
        self.root.mkdir(parents=True, exist_ok=True)
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        if final_dir.exists():
            raise FileExistsError(f"calibration bundle already exists: {final_dir}")
        reliability = {"_meta": {"schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION, "n_bins": len(report.reliability_bins[0]["bins"]) if report.reliability_bins and report.reliability_bins[0]["bins"] is not None else 0, "aggregation": "true_state_probability", "bin_edges": [i / 10 for i in range(11)]}, "predictors": list(report.reliability_bins)}
        distributions = {"schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION, "controls": [c.to_dict() for c in report.controls], "candidates": [c.to_dict() for c in report.candidates]}
        report_payload = report.to_dict()
        artifacts = {"calibration_report": report_payload, "metric_distributions": distributions, "reliability_bins": reliability}
        encoded = {name: _canonical_json(payload) for name, payload in artifacts.items()}
        artifact_hashes = {name: _sha256_bytes(data) for name, data in encoded.items()}
        bundle_hash = self._bundle_hash(artifact_hashes)
        manifest = {"schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION, "bundle_hash": bundle_hash, "corpus_manifest_hash": corpus_hash, "run_id": run_id, "artifacts": {name: {"hash": artifact_hashes[name], "size_bytes": len(encoded[name])} for name in sorted(encoded)}, "written_at": "deterministic-seal"}
        temp_dir = Path(tempfile.mkdtemp(prefix=f".tmp-{run_id}-{uuid.uuid4().hex}-", dir=str(final_dir.parent)))
        try:
            for name, data in encoded.items():
                (temp_dir / f"{name}.json").write_bytes(data)
            (temp_dir / "bundle.manifest").write_bytes(_canonical_json(manifest))
            if final_dir.exists():
                raise FileExistsError(f"calibration bundle already exists: {final_dir}")
            os.replace(temp_dir, final_dir)
        except Exception:
            if temp_dir.exists():
                for child in temp_dir.iterdir():
                    child.unlink()
                temp_dir.rmdir()
            raise
        return final_dir

    def read(self, *, corpus_manifest_hash: str, run_id: str) -> dict[str, Any]:
        bundle_dir = self.root / corpus_manifest_hash / run_id
        manifest_path = bundle_dir / "bundle.manifest"
        if not manifest_path.exists():
            raise ValueError("calibration bundle is incomplete: missing bundle.manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != CALIBRATION_ARTIFACT_SCHEMA_VERSION:
            raise ValueError("unsupported calibration bundle schema")
        if manifest.get("corpus_manifest_hash") != bundle_dir.parent.name:
            raise ValueError("bundle corpus hash does not match parent directory")
        actual: dict[str, str] = {}
        for name, metadata in manifest["artifacts"].items():
            path = bundle_dir / f"{name}.json"
            if not path.exists():
                raise ValueError(f"calibration bundle incomplete: missing {name}.json")
            data = path.read_bytes()
            digest = _sha256_bytes(data)
            if digest != metadata["hash"]:
                raise ValueError(f"calibration artifact hash mismatch: {name}")
            actual[name] = digest
        if self._bundle_hash(actual) != manifest["bundle_hash"]:
            raise ValueError("calibration bundle hash mismatch")
        return manifest
