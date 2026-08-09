from __future__ import annotations

import json

import pytest

from tiamat.calibration import CalibrationReport, CandidateDiagnostic, ControlMetricSet
from tiamat.calibration_artifacts import artifact_directory, write_calibration_artifacts


def make_report() -> CalibrationReport:
    digest = "a" * 64
    return CalibrationReport(
        corpus_manifest_hash=digest,
        label_provenance_hash="b" * 64,
        metric_contract_hash="c" * 64,
        controls=(ControlMetricSet(nll=1.9, brier=0.8, ece=0.2, label="uniform"),),
        candidates=(CandidateDiagnostic(model_id="M3", metrics={"nll": 1.1, "brier": 0.4, "ece": 0.08}, rows=10),),
        null_floor_check=True,
        spread_check={"threshold": 0.05, "observed": {"nll": 0.1, "brier": 0.1, "ece": 0.1}},
        ece_reliability_behavior="diagnostic fixture",
        inference_purity=True,
        decision="HOLD",
        decision_rationale="fixture",
        reliability_bins=(
            {
                "predictor": "uniform",
                "comparable": True,
                "reason": None,
                "bins": (
                    {"index": 0, "edge_lo": 0.0, "edge_hi": 0.1, "center": 0.05, "mean_confidence": 0.04, "empirical_accuracy": 0.06, "count": 4},
                    {"index": 1, "edge_lo": 0.1, "edge_hi": 0.2, "center": 0.15, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 2, "edge_lo": 0.2, "edge_hi": 0.3, "center": 0.25, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 3, "edge_lo": 0.3, "edge_hi": 0.4, "center": 0.35, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 4, "edge_lo": 0.4, "edge_hi": 0.5, "center": 0.45, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 5, "edge_lo": 0.5, "edge_hi": 0.6, "center": 0.55, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 6, "edge_lo": 0.6, "edge_hi": 0.7, "center": 0.65, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 7, "edge_lo": 0.7, "edge_hi": 0.8, "center": 0.75, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 8, "edge_lo": 0.8, "edge_hi": 0.9, "center": 0.85, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                    {"index": 9, "edge_lo": 0.9, "edge_hi": 1.0, "center": 0.95, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                ),
            },
        ),
    )


def test_artifact_path_is_manifest_and_run_bound(tmp_path):
    path = artifact_directory(tmp_path, "a" * 64, "run-1")
    assert path == tmp_path / "calibration_reports" / ("a" * 64) / "run-1"


def test_artifacts_are_json_and_content_addressed(tmp_path):
    report = make_report()
    path = write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
    saved = json.loads((path / "calibration_report.json").read_text(encoding="utf-8"))
    assert saved["calibration_hash"] == report.calibration_hash
    assert saved["report_version"] == report.report_version
    reliability = json.loads((path / "reliability_bins.json").read_text(encoding="utf-8"))
    assert reliability["_meta"]["n_bins"] == 10
    assert reliability["predictors"][0]["bins"][0]["count"] == 4
    assert len(reliability["predictors"][0]["bins"]) == 10


def test_existing_different_artifact_is_never_overwritten(tmp_path):
    report = make_report()
    path = write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
    target = path / "calibration_report.json"
    target.write_text("{\"tampered\": true}\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_calibration_artifacts(report, root=tmp_path, run_id="run-1")
