from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiamat.calibration import CalibrationBundleWriter, CalibrationReport, CandidateDiagnostic, ControlMetricSet


def _report() -> CalibrationReport:
    return CalibrationReport(
        corpus_manifest_hash="a" * 64,
        label_provenance_hash="b" * 64,
        metric_contract_hash="c" * 64,
        controls=(ControlMetricSet(nll=1.0, brier=0.4, ece=0.1, label="uniform"),),
        candidates=(CandidateDiagnostic(model_id="M0", metrics={"nll": 0.5, "brier": 0.2, "ece": 0.05}, rows=2),),
        null_floor_check=True,
        spread_check={"pass": False, "threshold": 0.05, "observed": {"nll": 0.0, "brier": 0.0, "ece": 0.0}},
        ece_reliability_behavior="diagnostic",
        inference_purity=True,
        decision="HOLD",
        decision_rationale="single candidate",
        reliability_bins=(
            {"predictor": "M0", "comparable": True, "reason": None, "bins": [
                {"index": 0, "edge_lo": 0.0, "edge_hi": 0.5, "center": 0.25, "mean_confidence": None, "empirical_accuracy": None, "count": 0},
                {"index": 1, "edge_lo": 0.5, "edge_hi": 1.0, "center": 0.75, "mean_confidence": 0.75, "empirical_accuracy": 1.0, "count": 2},
            ]},
            {"predictor": "M7", "comparable": False, "reason": "no verified native probability adapter", "bins": None},
        ),
    )


def test_bundle_is_sealed_and_readable(tmp_path: Path) -> None:
    writer = CalibrationBundleWriter(tmp_path)
    path = writer.write(_report(), run_id="run-1")
    assert (path / "bundle.manifest").exists()
    manifest = writer.read(corpus_manifest_hash="a" * 64, run_id="run-1")
    assert manifest["schema_version"] == 2
    assert manifest["bundle_hash"].startswith("sha256:")


def test_bundle_refuses_overwrite(tmp_path: Path) -> None:
    writer = CalibrationBundleWriter(tmp_path)
    writer.write(_report(), run_id="run-1")
    with pytest.raises(FileExistsError):
        writer.write(_report(), run_id="run-1")


def test_bundle_detects_tampering(tmp_path: Path) -> None:
    writer = CalibrationBundleWriter(tmp_path)
    path = writer.write(_report(), run_id="run-1")
    report_path = path / "calibration_report.json"
    payload = json.loads(report_path.read_text())
    payload["decision"] = "PROCEED"
    report_path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="hash mismatch"):
        writer.read(corpus_manifest_hash="a" * 64, run_id="run-1")


def test_bundle_requires_manifest(tmp_path: Path) -> None:
    bundle = tmp_path / ("a" * 64) / "run-1"
    bundle.mkdir(parents=True)
    with pytest.raises(ValueError, match="missing bundle.manifest"):
        CalibrationBundleWriter(tmp_path).read(corpus_manifest_hash="a" * 64, run_id="run-1")
