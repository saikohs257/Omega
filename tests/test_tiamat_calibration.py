from __future__ import annotations

import pytest

from tiamat import CalibrationReport, CandidateDiagnostic, ControlMetricSet, HoldoutExperiment, LabelProvenance, STATE_SPACE, corpus_fingerprint


HASH = "a" * 64


def _base_report(**overrides):
    payload = dict(
        corpus_manifest_hash=HASH,
        label_provenance_hash=HASH,
        metric_contract_hash=HASH,
        controls=(ControlMetricSet(1.0, 1.1, 1.2, "uniform"),),
        candidates=(CandidateDiagnostic("M3", {"nll": 0.9, "brier": 0.8, "ece": 0.7, "rows": 2}, 2),),
        null_floor_check=True,
        spread_check={"threshold": 0.05, "observed": {"nll": 0.1, "brier": 0.2, "ece": 0.3}, "pass": True},
        ece_reliability_behavior="balanced",
        inference_purity=True,
        decision="PROCEED",
        decision_rationale="ok",
    )
    payload.update(overrides)
    return CalibrationReport(**payload)


def _predictor(state: str):
    def predict(_row):
        return {candidate: (1.0 if candidate == state else 0.0) for candidate in STATE_SPACE}
    return predict


def test_calibration_report_is_identity_material() -> None:
    report = _base_report()
    payload = report.to_dict()
    assert payload["report_version"] == "calibration-report-v1.1"
    assert len(payload["calibration_hash"]) == 64


def test_calibration_report_hash_changes_with_content() -> None:
    a = _base_report().calibration_hash
    b = _base_report(decision_rationale="changed rationale").calibration_hash
    assert a != b


def test_holdout_calibration_report_requires_label_provenance() -> None:
    rows = [
        {"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
        {"timestamp": "2026-08-08T10:01:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
    ]
    experiment = HoldoutExperiment(label_provenance=LabelProvenance("proxy", "v1", "fixed boundary calibration", 1.0, ("mode",), "UNBOUND"))
    split = experiment.split_rows(rows)
    corpus_hash = corpus_fingerprint([r.to_mapping() for r in (*split.train, *split.validation, *split.test)])
    controls = {"uniform": _predictor("Q")}
    candidates = {"M3": _predictor("P")}
    report = experiment.calibration_report(rows, controls=controls, candidates=candidates, inference_purity=True, ece_reliability_behavior="balanced")
    # A single candidate cannot establish an inter-candidate spread; HOLD is
    # therefore the correct calibration outcome. This test is about provenance,
    # not about manufacturing a PROCEED decision from insufficient candidates.
    assert report.decision == "HOLD"
    assert report.spread_check["pass"] is False
    assert report.corpus_manifest_hash == corpus_hash
    assert report.label_provenance_hash
    assert report.metric_contract_hash


def test_holdout_calibration_report_rejects_label_corpus_mismatch() -> None:
    rows = [
        {"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
        {"timestamp": "2026-08-08T10:01:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
    ]
    controls = {"uniform": _predictor("Q")}
    candidates = {"M3": _predictor("P")}
    experiment = HoldoutExperiment(label_provenance=LabelProvenance("proxy", "v1", "fixed boundary calibration", 1.0, ("mode",), HASH))
    with pytest.raises(ValueError, match="label_provenance label_corpus_hash does not match holdout corpus"):
        experiment.calibration_report(rows, controls=controls, candidates=candidates, inference_purity=True, ece_reliability_behavior="unknown")


def test_calibration_api_rejects_precomputed_metric_bundles() -> None:
    experiment = HoldoutExperiment()
    rows = [{"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"}]
    with pytest.raises((TypeError, ValueError)):
        experiment.calibration_report(rows, controls={"uniform": {"nll": 1.0, "brier": 1.0, "ece": 1.0}}, candidates={}, inference_purity=True, ece_reliability_behavior="unknown")
