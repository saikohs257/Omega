from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Sequence
import json

from .calibration import CalibrationReport
from .calibration_artifacts import write_calibration_artifacts
from .corpus_snapshot import CorpusSnapshot
from .hf10 import ClaimRegistry, InformationSet
from .holdout import HoldoutExperiment
from .identification_registry import MODEL_REGISTRY
from .metric_contract import ProbabilityPredictor
from .telemetry import TelemetryRow


@dataclass(frozen=True, slots=True)
class DiagnosticPredictors:
    """Predictors supplied to the calibration diagnostic.

    Controls-only execution is intentionally permitted. It validates the frozen
    corpus -> metric contract -> artifact path before any candidate selector can run.
    """
    controls: Mapping[str, ProbabilityPredictor]
    candidates: Mapping[str, ProbabilityPredictor]

    def __post_init__(self) -> None:
        overlap = set(self.controls) & set(self.candidates)
        if overlap:
            raise ValueError(f"predictor IDs cannot be both control and candidate: {sorted(overlap)}")
        if not self.controls and not self.candidates:
            raise ValueError("at least one control or candidate predictor is required")


@dataclass(frozen=True, slots=True)
class DiagnosticRun:
    report: CalibrationReport
    artifact_path: Path


def load_json_rows(path: str | Path) -> tuple[dict, ...]:
    """Load a deterministic JSON array or JSONL corpus snapshot."""
    payload = Path(path).read_text(encoding="utf-8")
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in payload.splitlines() if line.strip()]
    else:
        rows = decoded
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("corpus must be a JSON array or JSONL object stream")
    return tuple(dict(row) for row in rows)


def _hf10_metadata(
    *,
    predictors: DiagnosticPredictors,
    information_set: InformationSet | None,
    claim_registry: ClaimRegistry | None,
) -> dict[str, object]:
    """Build deterministic HF10 metadata for the canonical report path.

    Missing HF10 context is explicitly ABSTAIN. It never implies PASS.
    The complete InformationSet and ClaimRegistry payloads are retained as
    authoritative evidence; derived hashes/status maps are convenience indexes.
    """
    if information_set is not None:
        information_set.validate()
        information_set_hash: str | None = information_set.information_set_hash
        registry_snapshot_hash: str | None = information_set.registry_snapshot_hash
        information_set_payload: dict[str, object] | None = information_set.to_dict()
    else:
        information_set_hash = None
        registry_snapshot_hash = None
        information_set_payload = None

    if claim_registry is not None:
        if information_set is not None and claim_registry.registry_snapshot_hash != information_set.registry_snapshot_hash:
            raise ValueError("claim_registry and information_set must reference the same frozen registry snapshot")
        claim_registry_hash: str | None = claim_registry.claim_registry_hash
        claim_status = claim_registry.status
        claim_rationale = claim_registry.rationale
        claims = sorted(
            (claim.to_dict() for claim in claim_registry.claims),
            key=lambda claim: (claim["predictor"], claim["claim_id"]),
        )
        claim_registry_payload: dict[str, object] | None = claim_registry.to_dict()
        claim_states = {claim["predictor"]: claim["status"] for claim in claims}
    else:
        claim_registry_hash = None
        claim_status = "ABSTAIN"
        claim_rationale = "claim registry not provided"
        claims = []
        claim_registry_payload = None
        claim_states = {}

    predictor_ids = tuple(sorted(set(predictors.controls) | set(predictors.candidates)))
    per_predictor = {model_id: claim_states.get(model_id, "ABSTAIN") for model_id in predictor_ids}
    return {
        "hf10_information_set": information_set_payload,
        "hf10_information_set_hash": information_set_hash,
        "hf10_claim_registry": claim_registry_payload,
        "hf10_claim_registry_hash": claim_registry_hash,
        "hf10_claim_registry_snapshot_hash": registry_snapshot_hash,
        "hf10_claim_status": claim_status,
        "hf10_claim_rationale": claim_rationale,
        "hf10_claims": claims,
        "hf10_claim_state_by_predictor": per_predictor,
    }


def run_diagnostic(
    rows: Sequence[Mapping[str, object] | TelemetryRow],
    *,
    experiment: HoldoutExperiment,
    predictors: DiagnosticPredictors,
    run_id: str,
    artifact_root: str | Path,
    inference_purity: bool = True,
    ece_reliability_behavior: str = "",
    information_set: InformationSet | None = None,
    claim_registry: ClaimRegistry | None = None,
) -> DiagnosticRun:
    """Run calibration diagnostics and persist them through the single canonical writer.

    No model selection occurs here. HF10 metadata is attached to the same
    CalibrationReport that every other diagnostic caller persists.
    """
    if not inference_purity:
        raise ValueError("real diagnostic execution requires inference_purity=True")
    if not ece_reliability_behavior.strip():
        raise ValueError("ece_reliability_behavior is required before diagnostic execution")

    source = tuple(row.to_mapping() if isinstance(row, TelemetryRow) else dict(row) for row in rows)
    snapshot = CorpusSnapshot.freeze(source)
    snapshot.verify()
    report = experiment.calibration_report(
        snapshot.rows,
        controls=predictors.controls,
        candidates=predictors.candidates,
        inference_purity=inference_purity,
        ece_reliability_behavior=ece_reliability_behavior,
    )
    snapshot.verify()
    spread_check = dict(report.spread_check)
    spread_check.update(_hf10_metadata(
        predictors=predictors,
        information_set=information_set,
        claim_registry=claim_registry,
    ))
    report = replace(report, spread_check=spread_check)
    artifact_path = write_calibration_artifacts(report, root=artifact_root, run_id=run_id)
    return DiagnosticRun(report=report, artifact_path=artifact_path)


def registry_model_ids() -> tuple[str, ...]:
    return tuple(sorted(MODEL_REGISTRY))
