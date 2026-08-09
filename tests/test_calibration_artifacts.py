from __future__ import annotations

from pathlib import Path

import pytest

from tiamat import (
    CalibrationReport,
    CandidateDiagnostic,
    ControlMetricSet,
    artifact_directory,
    load_calibration_bundle,
    write_calibration_artifacts,
)

HASH = "a" * 64


def _report() -> CalibrationReport:
    return CalibrationReport(
        corpus_manifest_hash=HASH,
        label_provenance_hash=HASH,
        metric_contract_hash=HASH,
        controls=(ControlMetricSet(1.0, 1.1, 1.2, "uniform"),),
        candidates=(CandidateDiagnostic("M3", {"nll": 0.9, "brier": 0.8, "ece": 0.7}, 2),),
        null_floor_check=True,
        spread_check={"threshold": 0.05, "observed": {"nll": 0.1, "brier": 0.2, "ece": 0.3}, "pass": True},
        ece_reliability_behavior="balanced",
        inference_purity=True,
        decision="PROCEED",
        decision_rationale="ok",
        reliability_bins=(
            {
                "predictor": "uniform",
                "comparable": True,
                "reason": None,
                "bins": (
                    {"index": 0, "edge_lo": 0.0, "edge_hi": 0.5, "center": 0.25, "mean_confidence": 0.2, "empirical_accuracy": 0.1, "count": 3},
                    {"index": 1, "edge_lo": 0.5, "edge_hi": 1.0, "center": 0.75, "mean_confidence": 0.8, "empirical_accuracy": 0.9, "count": 2},
                ),
            },
        ),
    )


def test_artifact_directory_targets_calibration_reports(tmp_path: Path) -> None:
    directory = artifact_directory(tmp_path, HASH, "run-1")
    assert directory == tmp_path / "calibration_reports" / HASH / "run-1"

    with pytest.raises(ValueError, match="SHA-256"):
        artifact_directory(tmp_path, "bad-hash", "run-1")


def test_write_and_load_calibration_bundle(tmp_path: Path) -> None:
    report = _report()
    bundle_dir = write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
    assert bundle_dir == artifact_directory(tmp_path, HASH, "run-1")
    assert (bundle_dir / "bundle.manifest").exists()

    loaded = load_calibration_bundle(tmp_path, HASH, "run-1")
    assert loaded["manifest"]["corpus_manifest_hash"] == HASH
    assert loaded["calibration_report"]["calibration_hash"] == report.calibration_hash
    assert loaded["reliability_bins"]["_meta"]["n_bins"] == 2
    assert loaded["reliability_bins"]["predictors"][0]["bins"][0]["count"] == 3


def test_write_calibration_bundle_refuses_overwrite(tmp_path: Path) -> None:
    report = _report()
    write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
    with pytest.raises(FileExistsError):
        write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
