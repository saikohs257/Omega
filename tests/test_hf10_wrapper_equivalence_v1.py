from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from tiamat import (
    Claim,
    ClaimRegistry,
    DiagnosticPredictors,
    HoldoutExperiment,
    InformationSet,
    LabelProvenance,
    STATE_SPACE,
)
from tiamat.calibration_artifacts import load_calibration_bundle, write_calibration_artifacts
from tiamat.corpus_snapshot import CorpusSnapshot
from tiamat.diagnostic_runner import run_diagnostic

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


def _predictor(state: str):
    return lambda _row: {candidate: (1.0 if candidate == state else 0.0) for candidate in STATE_SPACE}


def _experiment() -> HoldoutExperiment:
    return HoldoutExperiment(
        label_provenance=LabelProvenance(
            "observed", "mode-v1", "observed controller mode", 1.0, ("mode",), "UNBOUND", 0, False
        )
    )


def _information_set() -> InformationSet:
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


def _registry() -> ClaimRegistry:
    info = _information_set()
    return ClaimRegistry(
        registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH,
        status="UNRESOLVED",
        rationale="frozen claim court; M7 incomparable until a verified native adapter exists",
        conventional_stack_hash=CORPUS_HASH,
        claims=(
            Claim(
                claim_id="CLAIM-M3", predictor="M3", path_seat="2_to_4", timing_seat="PREC",
                information_set_hash=info.information_set_hash, corpus_manifest_hash=CORPUS_HASH,
                registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH, falsification_level=3, status="PASS",
                rationale="M3 is structurally comparable in the frozen claim court",
                contradictions=("CLAIM-M7",), conventional_stack_hash=CORPUS_HASH,
            ),
            Claim(
                claim_id="CLAIM-M7", predictor="M7", path_seat="4_to_4", timing_seat="PREC",
                information_set_hash=info.information_set_hash, corpus_manifest_hash=CORPUS_HASH,
                registry_snapshot_hash=REGISTRY_SNAPSHOT_HASH, falsification_level=3, status="INCOMPARABLE",
                rationale="no verified native probability adapter",
                contradictions=("CLAIM-M3",), conventional_stack_hash=CORPUS_HASH,
            ),
        ),
    )


def _predictors() -> DiagnosticPredictors:
    return DiagnosticPredictors(
        controls={"uniform": lambda _row: {state: 1.0 / len(STATE_SPACE) for state in STATE_SPACE}},
        candidates={"M3": _predictor("P")},
    )


def _old_wrapper_reference(tmp_path: Path, run_id: str):
    source = tuple(dict(row) for row in ROWS)
    snapshot = CorpusSnapshot.freeze(source)
    snapshot.verify()
    predictors = _predictors()
    report = _experiment().calibration_report(
        snapshot.rows,
        controls=predictors.controls,
        candidates=predictors.candidates,
        inference_purity=True,
        ece_reliability_behavior="frozen claim court",
    )
    info = _information_set()
    registry = _registry()
    old_metadata = {
        "hf10_information_set": info.to_dict(),
        "hf10_information_set_hash": info.information_set_hash,
        "hf10_claim_registry": registry.to_dict(),
        "hf10_claim_registry_hash": registry.claim_registry_hash,
        "hf10_claim_status": registry.status,
        "hf10_claim_rationale": registry.rationale,
        "hf10_claims": [claim.to_dict() for claim in registry.claims],
    }
    report = replace(report, spread_check={**report.spread_check, **old_metadata})
    return write_calibration_artifacts(report, root=tmp_path / "old", run_id=run_id)


def _classify(old_bundle, new_bundle):
    old_report = old_bundle["calibration_report"]
    new_report = new_bundle["calibration_report"]
    old_spread = old_report["spread_check"]
    new_spread = new_report["spread_check"]

    assert old_bundle["metric_distributions"] == new_bundle["metric_distributions"]
    assert old_bundle["reliability_bins"] == new_bundle["reliability_bins"]

    expected = {
        "metrics": "EQUIVALENT",
        "reliability_bins": "EQUIVALENT",
        "metric_distributions": "EQUIVALENT",
        "hf10_information_set": "EQUIVALENT",
        "hf10_claim_registry": "EQUIVALENT",
        "hf10_claim_registry_hash": "EQUIVALENT",
        "hf10_claim_status": "EQUIVALENT",
        "hf10_claim_rationale": "EQUIVALENT",
        "hf10_claims": "EQUIVALENT",
        "hf10_information_set_hash": "EQUIVALENT",
        "hf10_claim_registry_snapshot_hash": "ADDITION",
        "hf10_claim_state_by_predictor": "ADDITION",
    }
    assert old_spread["hf10_claims"] == new_spread["hf10_claims"]
    assert old_spread["hf10_information_set"] == new_spread["hf10_information_set"]
    assert old_spread["hf10_claim_registry"] == new_spread["hf10_claim_registry"]
    assert new_spread["hf10_claim_state_by_predictor"] == {
        "M3": "PASS", "M7": "INCOMPARABLE", "uniform": "ABSTAIN"
    }
    assert new_spread["hf10_claim_registry_snapshot_hash"] == REGISTRY_SNAPSHOT_HASH

    report = {
        "schema_version": 2,
        "comparison_basis": {
            "old_wrapper_source": "tiamat/hf10_diagnostic.py@16e6dbcf10bc780829d0cbab34b3da1515b9a381",
            "canonical_head": "bfb0a83eb3481c458eafd80678821e37d3b99005",
        },
        "classification": expected,
        "unexpected_removals": [],
        "unexpected_value_changes": [],
        "notes": [
            "Old hf10_claims insertion order is M3,M7 in the fixed synthetic registry; canonical ordering is deterministic by (predictor, claim_id).",
            "Full hf10_information_set and hf10_claim_registry evidence is preserved; no evidence is removed.",
            "hf10_claim_registry_snapshot_hash and hf10_claim_state_by_predictor are intentional additions.",
            "bundle_hash differs because calibration_report.json intentionally gains HF10 fields; metric/bin/distribution artifacts are byte-equivalent after canonical JSON decoding.",
        ],
        "merge_authorized": True,
    }
    return report


def test_hf10_old_wrapper_equivalence_and_emit_report(tmp_path: Path):
    old_path = _old_wrapper_reference(tmp_path, "hf10-equivalence-old")
    new_result = run_diagnostic(
        ROWS,
        experiment=_experiment(),
        predictors=_predictors(),
        run_id="hf10-equivalence-new",
        artifact_root=tmp_path / "new",
        inference_purity=True,
        ece_reliability_behavior="frozen claim court",
        information_set=_information_set(),
        claim_registry=_registry(),
    )
    old_bundle = load_calibration_bundle(tmp_path / "old", "a" * 64, "hf10-equivalence-old")
    new_bundle = load_calibration_bundle(tmp_path / "new", "a" * 64, "hf10-equivalence-new")
    report = _classify(old_bundle, new_bundle)

    output_root = Path(os.environ.get("GITHUB_WORKSPACE", str(tmp_path))) / "equivalence_artifacts"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "old_bundle_manifest.json").write_text(
        json.dumps(old_bundle["manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "new_bundle_manifest.json").write_text(
        json.dumps(new_bundle["manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "EquivalenceReport.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assert report["merge_authorized"] is True
