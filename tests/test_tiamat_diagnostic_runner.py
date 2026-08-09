from __future__ import annotations

import pytest

from tiamat import HoldoutExperiment, LabelProvenance, STATE_SPACE
from tiamat.diagnostic_runner import DiagnosticPredictors, run_diagnostic


ROWS = (
    {"timestamp": "2026-08-08T10:00:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
    {"timestamp": "2026-08-08T10:01:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
    {"timestamp": "2026-08-08T10:02:00Z", "B": 0.4, "V": 0.2, "D": 0.1, "tau_D": 0.0, "tau_mode": 1.0, "mode": "E"},
    {"timestamp": "2026-08-08T10:03:00Z", "B": 0.5, "V": 0.1, "D": 0.2, "tau_D": 1.0, "tau_mode": 1.0, "mode": "H"},
    {"timestamp": "2026-08-08T10:04:00Z", "B": 0.3, "V": -0.1, "D": 0.1, "tau_D": 2.0, "tau_mode": 1.0, "mode": "R"},
    {"timestamp": "2026-08-08T10:05:00Z", "B": 0.1, "V": -0.1, "D": 0.0, "tau_D": 3.0, "tau_mode": 1.0, "mode": "Rf"},
)


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


def test_diagnostic_runner_uses_canonical_artifact_writer(tmp_path):
    result = run_diagnostic(
        ROWS,
        experiment=experiment(),
        predictors=DiagnosticPredictors(
            controls={"uniform": lambda _row: {state: 1.0 / len(STATE_SPACE) for state in STATE_SPACE}},
            candidates={"M3": predictor("P"), "M4": predictor("E")},
        ),
        run_id="diagnostic-1",
        artifact_root=tmp_path,
        inference_purity=True,
        ece_reliability_behavior="fixture-only; inspect real run before selection",
    )
    assert result.artifact_path.exists()
    assert (result.artifact_path / "bundle.manifest").exists()
    assert result.report.decision == "HOLD"


def test_controls_only_diagnostic_is_valid_and_never_proceeds(tmp_path):
    result = run_diagnostic(
        ROWS,
        experiment=experiment(),
        predictors=DiagnosticPredictors(
            controls={"uniform": lambda _row: {state: 1.0 / len(STATE_SPACE) for state in STATE_SPACE}},
            candidates={},
        ),
        run_id="controls-only",
        artifact_root=tmp_path,
        inference_purity=True,
        ece_reliability_behavior="controls-only infrastructure validation; no candidate selection",
    )
    assert result.artifact_path.exists()
    assert result.report.candidates == ()
    assert result.report.decision == "HOLD"
    assert result.report.spread_check["candidate_count"] == 0


def test_diagnostic_runner_rejects_empty_predictor_set():
    with pytest.raises(ValueError, match="at least one control or candidate"):
        DiagnosticPredictors(controls={}, candidates={})


def test_diagnostic_runner_rejects_impure_execution(tmp_path):
    with pytest.raises(ValueError, match="inference_purity"):
        run_diagnostic(
            ROWS,
            experiment=experiment(),
            predictors=DiagnosticPredictors(controls={}, candidates={"M3": predictor("P")}),
            run_id="diagnostic-impure",
            artifact_root=tmp_path,
            inference_purity=False,
            ece_reliability_behavior="fixture",
        )
