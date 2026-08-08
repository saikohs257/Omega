from __future__ import annotations

from erk.core import Action, Authority, EpistemicState, PolicyConfig, Supervisor


def test_cycles_have_structural_precedence_over_optimization() -> None:
    state = EpistemicState(cycles=(("a", "b", "a"),))
    supervisor = Supervisor()
    assert supervisor.supervise(state) == Action.REJECT


def test_high_strain_quarantines_before_cost_selection() -> None:
    state = EpistemicState(strain=0.95)
    supervisor = Supervisor(PolicyConfig(cost_weights={Action.REJECT: 0.0, Action.QUARANTINE: 1.0}))
    assert supervisor.supervise(state) == Action.QUARANTINE


def test_calibration_failure_escalates_before_normal_block() -> None:
    state = EpistemicState(calibration_error=0.50)
    assert Supervisor().supervise(state) == Action.ESCALATE


def test_depth_bound_escalates_before_branching() -> None:
    state = EpistemicState(unsupported_depth=8)
    assert Supervisor().supervise(state) == Action.ESCALATE


def test_branch_bound_escalates_when_capacity_is_exhausted() -> None:
    state = EpistemicState(active_branches=16)
    assert Supervisor().supervise(state) == Action.BLOCK


def test_execute_authority_has_execution_precedence_when_all_safety_gates_pass() -> None:
    state = EpistemicState(authority=Authority.EXECUTE)
    assert Supervisor().supervise(state) == Action.ENABLE_EXECUTION
