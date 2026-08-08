from __future__ import annotations

from erk import Action, Authority, ConstitutionalKernel, EpistemicState


def admissible(state: EpistemicState) -> bool:
    return Action.ENABLE_EXECUTION in ConstitutionalKernel().supervisor.safe_actions(state)


def test_strain_boundary() -> None:
    assert admissible(EpistemicState(authority=Authority.EXECUTE, strain=0.799999))
    assert not admissible(EpistemicState(authority=Authority.EXECUTE, strain=0.80))


def test_depth_boundary() -> None:
    assert admissible(EpistemicState(authority=Authority.EXECUTE, unsupported_depth=7))
    assert not admissible(EpistemicState(authority=Authority.EXECUTE, unsupported_depth=8))


def test_calibration_boundary() -> None:
    assert admissible(EpistemicState(authority=Authority.EXECUTE, calibration_error=0.249999))
    assert not admissible(EpistemicState(authority=Authority.EXECUTE, calibration_error=0.25))


def test_branch_boundary() -> None:
    assert admissible(EpistemicState(authority=Authority.EXECUTE, active_branches=16))
    assert not admissible(EpistemicState(authority=Authority.EXECUTE, active_branches=17))
