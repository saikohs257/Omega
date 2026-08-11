from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow
from tools.dvqt_probability_benchmark import benchmark


def rows():
    return [
        TelemetryRow(D=0.1, V=0.8, B=1.0, mode=TiamatMode.PRECURSOR, tau_mode=2.0),
        TelemetryRow(D=0.1, V=0.8, B=1.0, mode=TiamatMode.EXCITATION, tau_mode=2.0),
        TelemetryRow(D=0.1, V=0.8, B=1.0, mode=TiamatMode.PRECURSOR, tau_mode=2.0),
        TelemetryRow(D=0.1, V=0.8, B=1.0, mode=TiamatMode.EXCITATION, tau_mode=2.0),
    ]


def test_full_scoreboard_contains_required_metrics():
    report = benchmark({"fixture": rows()})
    metrics = report["DVQT+B"]
    assert metrics["coverage"] > 0
    assert 0 <= metrics["brier"] <= 1
    assert metrics["log_loss"] >= 0
    assert 0 <= metrics["calibration_error"] <= 1
    assert 0 <= metrics["auc"] <= 1
    assert 0 <= metrics["pr_auc"] <= 1


def test_complexity_is_dimension_count():
    report = benchmark({"fixture": rows()})
    assert report["DV+B"]["dimensions"] == 3
    assert report["DVQT+B"]["dimensions"] == 5
