from tiamat.tournament_round2 import run_round_two


def test_round_two_delay_is_diagnostic_only() -> None:
    result = run_round_two()
    assert result.audits
    for audit in result.audits:
        # A delay failure may be reported, but it cannot be the reason the
        # candidate fails the Round-2 gate.
        if audit.delayed_status == "FAILED":
            assert "delayed" not in audit.failed


def test_round_two_requires_inverse_failure_and_attenuation_survival() -> None:
    result = run_round_two()
    for audit in result.audits:
        assert (audit.passed == ("attenuated" in audit.survived and "inverse" in audit.failed))
