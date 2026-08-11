"""End-to-end checks for the blinded adversarial tournament harness."""
from __future__ import annotations

from tiamat.tournament_lab import run_adversarial_tournament


def test_full_adversarial_tournament_has_no_unexpected_failures() -> None:
    report = run_adversarial_tournament()
    assert len(report.audits) == 12
    assert report.passed
    assert not report.failures


def test_adversarial_tournament_keeps_no_signal_unresolved() -> None:
    report = run_adversarial_tournament()
    no_signal = next(a for a in report.audits if a.expectation.world_name == "no_signal")
    assert no_signal.result.decision.status == "UNRESOLVED"
    assert no_signal.result.decision.selected_model_id is None


def test_adversarial_tournament_recovers_interaction_and_calibration_controls() -> None:
    report = run_adversarial_tournament()
    interaction = next(a for a in report.audits if a.expectation.world_name == "interaction_only")
    calibration = next(a for a in report.audits if a.expectation.world_name == "calibration_deception")
    assert interaction.result.decision.selected_model_id == "A_x_B"
    assert calibration.result.decision.selected_model_id == "calibrated"
