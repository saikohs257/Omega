from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from tiamat import HoldoutExperiment, InformationSet, Claim, ClaimRegistry, LabelProvenance, STATE_SPACE
from tiamat.hf10_diagnostic import run_hf10_diagnostic


ROWS = (
    {"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
    {"timestamp": "2026-08-08T10:01:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
    {"timestamp": "2026-08-08T10:02:00Z", "B": 0.4, "V": 0.2, "D": 0.1, "tau_D": 0.0, "tau_mode": 1.0, "mode": "E"},
    {"timestamp": "2026-08-08T10:03:00Z", "B": 0.5, "V": 0.1, "D": 0.2, "tau_D": 1.0, "tau_mode": 1.0, "mode": "H"},
    {"timestamp": "2026-08-08T10:04:00Z", "B": 0.3, "V": -0.1, "D": 0.1, "tau_D": 2.0, "tau_mode": 1.0, "mode": "R"},
    {"timestamp": "2026-08-08T10:05:00Z", "B": 0.1, "V": -0.1, "D": 0.0, "tau_D": 3.0, "tau_mode": 1.0, "mode": "Rf"},
)

REGISTRY_SNAPSHOT_HASH = "d" * 64
CORPUS_HASH = "a" * 64
PROVENANCE_HASH = "b" * 64
CLAIM_REGISTRY_HASH = "e" * 64


def predictor(state: str):
    def predict(_row):
        return {candidate: (1.0 if candidate == state else 0.0) for candidate in STATE_SPACE}
    return predict


def experiment() -> HoldoutExperiment:
    return HoldoutExperiment(
        label_provenance=LabelProvenance(
            "observed", "mode-v1", "observed controller mode", 1.0, ("mode",), "UNBOUND", 0, False
        )
    )


def hf10_information_set() -> InformationSet:
    return InformationSet(
        timing_seat="PREC",
        observation_cutoff=datetime(2026, 8, 8, 10, 5, tzinfo=timezone.utc),
        allowed_lookback=timedelta(hours=24),
        forbidden_future_window=timedelta(0),
        label_offset=timedelta(0),
        feature_snapshot_hash=CORPUS_HASH,
        provenance_hash=PROVENANCE_HASH,
        corpus_manifest_hash=CORPUS_HASH,
        registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH,
    )


def hf10_claim_registry() -> ClaimRegistry:
    return ClaimRegistry(
        registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH,
        status="UNRESOLVED",
        rationale="frozen claim court; M7 incomparable until a verified native adapter exists",
        conventional_stack_hash=CORPUS_HASH,
        claims=(
            Claim(
                claim_id="CLAIM-M3",
                predictor="M3",
                path_seat="2_to_4",
                timing_seat="PREC",
                information_set_hash=hf10_information_set().information_set_hash,
                corpus_manifest_hash=CORPUS_HASH,
                registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH,
                falsification_level=3,
                status="PASS",
                rationale="M3 is structurally comparable in the frozen claim court",
                contradictions=("CLAIM-M7",),
                conventional_stack_hash=CORPUS_HASH,
            ),
            Claim(
                claim_id="CLAIM-M7",
                predictor="M7",
                path_seat="4_to_4",
                timing_seat="PREC",
                information_set_hash=hf10_information_set().information_set_hash,
                corpus_manifest_hash=CORPUS_HASH,
                registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH,
                falsification_level=3,
                status="INCOMPARABLE",
                rationale="no verified native probability adapter",
                contradictions=("CLAIM-M3",),
                conventional_stack_hash=CORPUS_HASH,
            ),
        ),
    )


def test_hf10_accepts_frozen_claim_inputs_and_seals_court_state(tmp_path: Path):
    info = hf10_information_set()
    registry = hf10_claim_registry()
    result = run_hf10_diagnostic(
        ROWS,
        experiment=experiment(),
        predictors=DiagnosticPredictors(
            controls={"uniform": lambda _row: {state: 1.0 / len(STATE_SPACE) for state in STATE_SPACE}},
            candidates={"M3": predictor("P")},
        ),
        run_id="hf10-diagnostic-1",
        artifact_root=tmp_path,
        inference_purity=True,
        ece_reliability_behavior="frozen claim court",
        information_set=info,
        claim_registry=registry,
    )
    assert result.artifact_path.exists()
    assert result.report.decision in {"HOLD", "PROCEED"}
    assert result.report.spread_check["hf10_information_set_hash"] == info.information_set_hash
    assert result.report.spread_check["hf10_claim_registry_hash"] == registry.claim_registry_hash
    assert result.report.spread_check["hf10_claim_status"] == "UNRESOLVED"
    assert any(claim["claim_id"] == "CLAIM-M7" and claim["status"] == "INCOMPARABLE" for claim in result.report.spread_check["hf10_claims"])
    saved = json.loads((result.artifact_path / "calibration_report.json").read_text(encoding="utf-8"))
    assert saved["spread_check"]["hf10_claim_registry_hash"] == registry.claim_registry_hash
    assert saved["spread_check"]["hf10_claim_status"] == "UNRESOLVED"


def test_hf10_rejects_missing_evidence_context():
    with pytest.raises(ValueError, match="at least one control or candidate"):
        run_hf10_diagnostic(
            ROWS,
            experiment=experiment(),
            predictors=DiagnosticPredictors(controls={}, candidates={}),
            run_id="hf10-empty",
            artifact_root=tmp_path if False else "/tmp",
            inference_purity=True,
            ece_reliability_behavior="frozen claim court",
        )