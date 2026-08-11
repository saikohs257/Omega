from tiamat.tournament_round2 import run_round_two


def test_round_two_records_deliberate_kill_and_attenuation_separately() -> None:
    result = run_round_two()
    assert result.first_round_selected >= 1
    assert result.stressed == len(result.audits)
    for audit in result.audits:
        assert "inverse" in audit.survived or "inverse" in audit.failed
        assert "attenuated" in audit.survived or "attenuated" in audit.failed
        assert audit.expected_kills == ("inverse",)
        assert audit.passed == ("inverse" in audit.failed and "attenuated" in audit.survived)


def test_round_two_delay_is_diagnostic_only() -> None:
    result = run_round_two()
    for audit in result.audits:
        assert "delayed" in audit.survived or "delayed" in audit.failed
