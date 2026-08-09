from __future__ import annotations

import pytest

from tiamat.calibration import CalibrationDiagnostic
from tiamat.metric_contract import MetricContract, ProbabilityContract
from tiamat.telemetry import TelemetryAdapter


STATE_SPACE = ("Q", "P", "E", "C", "H", "R", "Rf")


class DummyPredictor:
    def __init__(self, state: str = "Q") -> None:
        self.state = state

    def __call__(self, _row):
        return {candidate: (1.0 if candidate == self.state else 0.0) for candidate in STATE_SPACE}


def _diagnostic() -> CalibrationDiagnostic:
    return CalibrationDiagnostic(
        MetricContract(ProbabilityContract(STATE_SPACE)),
        ProbabilityContract(STATE_SPACE),
        TelemetryAdapter(),
    )


def _rows():
    return [
        {"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
        {"timestamp": "2026-08-08T10:01:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
        {"timestamp": "2026-08-08T10:02:00Z", "B": 0.4, "V": 0.2, "D": 0.1, "tau_D": 0.0, "tau_mode": 1.0, "mode": "E"},
    ]


def test_hf10_accepts_frozen_claim_inputs_and_registers_comparable_rows():
    report = _diagnostic().create_report(
        corpus_manifest_hash="a" * 64,
        label_provenance_hash="b" * 64,
        metric_contract_hash="c" * 64,
        rows=_rows(),
        controls={"uniform": DummyPredictor("Q")},
        candidates={"M3": DummyPredictor("P")},
        inference_purity=True,
        ece_reliability_behavior="frozen claim court",
        incomparable={"M7": "no verified native probability adapter"},
    )
    assert report.decision in {"HOLD", "PROCEED"}
    assert report.candidates[0].comparable is True
    assert report.candidates[1].comparable is False
    assert report.candidates[1].reason == "no verified native probability adapter"
    assert any(bucket["predictor"] == "M7" and bucket["comparable"] is False for bucket in report.reliability_bins)


def test_hf10_rejects_missing_evidence_context():
    diag = _diagnostic()
    with pytest.raises(ValueError, match="at least one control or candidate"):
        diag.create_report(
            corpus_manifest_hash="a" * 64,
            label_provenance_hash="b" * 64,
            metric_contract_hash="c" * 64,
            rows=_rows(),
            controls={},
            candidates={},
            inference_purity=True,
            ece_reliability_behavior="frozen claim court",
        )
