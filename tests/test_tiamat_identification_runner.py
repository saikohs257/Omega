from __future__ import annotations

from tiamat import (
    IDENTIFICATION_RUNNER_VERSION,
    IdentificationRunner,
    TelemetryAdapter,
    TelemetryRow,
    TiamatMode,
)


def test_identification_runner_version_is_explicit_and_exported() -> None:
    assert IDENTIFICATION_RUNNER_VERSION == "v1.1"


def test_telemetry_row_projects_and_round_trips() -> None:
    row = TelemetryRow.from_mapping(
        {
            "B": 0.4,
            "V": -0.2,
            "D": 0.3,
            "tau_D": 5.0,
            "tau_mode": 2.0,
            "Phi": 0.1,
            "mode": "E",
            "timestamp": "2026-08-08T10:00:00Z",
        }
    )

    assert row.mode is TiamatMode.EXCITATION
    assert row.project("M3") == {"B": 0.4, "V": -0.2, "D": 0.3}
    assert TelemetryRow.from_mapping(row.to_mapping()) == row


def test_runner_evaluates_candidate_trials_without_hardcoding_runtime_conclusions() -> None:
    rows = [
        {"B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
        {"B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "P"},
    ]

    runner = IdentificationRunner()
    report = runner.evaluate(rows, model_ids=("M0", "M1", "M3", "M7"))

    assert report.winner is not None
    assert report.winner.model_id in {"M0", "M1", "M3", "M7"}
    trial = next(trial for trial in report.trials if trial.model_id == "M3")
    assert trial.coverage == 1.0
    assert trial.supported_rows == 2
    assert trial.transition_error is not None


def test_adapter_uses_registry_axes_and_control_axes() -> None:
    adapter = TelemetryAdapter()
    row = {"B": 0.5, "V": 0.25, "D": 0.75, "tau_D": 3.0, "tau_mode": 4.0, "Phi": 0.9}

    assert adapter.frame([row], "M3")[0] == {"B": 0.5, "V": 0.25, "D": 0.75}
    assert adapter.frame([row], "M7")[0] == {"B": 0.5, "V": 0.25, "D": 0.75, "tau_D": 3.0, "tau_mode": 4.0, "Phi": 0.9}
