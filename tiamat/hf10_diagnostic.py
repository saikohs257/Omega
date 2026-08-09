from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping, Sequence

from .calibration import CalibrationReport
from .calibration_artifacts import write_calibration_artifacts
from .corpus_snapshot import CorpusSnapshot
from .diagnostic_runner import DiagnosticPredictors, DiagnosticRun
from .experiment_manifest import canonical_hash
from .hf10 import ClaimRegistry, InformationSet
from .holdout import HoldoutExperiment
from .telemetry import TelemetryRow


def _hf10_metadata(
    *,
    information_set: InformationSet | None,
    claim_registry: ClaimRegistry | None,
) -> dict[str, object]:
    if information_set is not None:
        information_set.validate()
        info_hash = information_set.information_set_hash
        info_payload = information_set.to_dict()
    else:
        info_hash = canonical_hash({"kind": "InformationSet", "status": "UNBOUND"})
        info_payload = {"status": "UNBOUND", "information_set_hash": info_hash}

    if claim_registry is not None:
        if information_set is not None and claim_registry.registry_snapshot_hash != information_set.registry_snapshot_hash:
            raise ValueError("claim_registry and information_set must reference the same frozen registry snapshot")
        claim_hash = claim_registry.claim_registry_hash
        claim_status = claim_registry.status
        claim_rationale = claim_registry.rationale
        claim_payload = [claim.to_dict() for claim in claim_registry.claims]
        claim_registry_payload = claim_registry.to_dict()
    else:
        claim_hash = canonical_hash({"kind": "ClaimRegistry", "status": "UNRESOLVED"})
        claim_status = "UNRESOLVED"
        claim_rationale = "claim registry not provided"
        claim_payload = []
        claim_registry_payload = {"status": claim_status, "rationale": claim_rationale, "claim_registry_hash": claim_hash}

    return {
        "hf10_information_set": info_payload,
        "hf10_information_set_hash": info_hash,
        "hf10_claim_registry": claim_registry_payload,
        "hf10_claim_registry_hash": claim_hash,
        "hf10_claim_status": claim_status,
        "hf10_claim_rationale": claim_rationale,
        "hf10_claims": claim_payload,
    }


def enrich_hf10_report(
    report: CalibrationReport,
    *,
    information_set: InformationSet | None = None,
    claim_registry: ClaimRegistry | None = None,
) -> CalibrationReport:
    """Return a calibration report with HF10 court state embedded into spread_check."""
    metadata = _hf10_metadata(information_set=information_set, claim_registry=claim_registry)
    spread_check = dict(report.spread_check)
    spread_check.update(metadata)
    return replace(report, spread_check=spread_check)


def run_hf10_diagnostic(
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
    """Run diagnostics and seal HF10 court state into the persisted bundle."""
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
    hf10_report = enrich_hf10_report(report, information_set=information_set, claim_registry=claim_registry)
    artifact_path = write_calibration_artifacts(hf10_report, root=artifact_root, run_id=run_id)
    return DiagnosticRun(report=hf10_report, artifact_path=artifact_path)
