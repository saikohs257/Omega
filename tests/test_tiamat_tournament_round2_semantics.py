from tiamat.tournament_round2 import run_round_two


def test_round_two_requires_kill_and_attenuation_survival() -> None:
    result = run_round_two()
    assert result.first_round_selected >= 1
    assert result.stressed == len(result.audits)
    for audit in result.audits:
        assert "inverse" in audit.failed
        assert "attenuated" in audit.survived
        assert audit.passed


def test_round_two_does_not_make_delay_a_universal_gate() -> None:
    result = run_round_two()
    assert all("delayed" in audit.survived or "delayed" in audit.failed for audit in result.audits)
    assert any("delayed" in audit.failed for audit in result.audits)
