from __future__ import annotations

import math

import pytest

from erk.core import Action, Authority, EpistemicState, PolicyConfig, Supervisor, compute_strain


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


def test_branch_bound_blocks_when_capacity_is_exhausted() -> None:
    state = EpistemicState(active_branches=16)
    assert Supervisor().supervise(state) == Action.BLOCK


def test_execute_authority_has_execution_precedence_when_all_safety_gates_pass() -> None:
    state = EpistemicState(authority=Authority.EXECUTE)
    assert Supervisor().supervise(state) == Action.ENABLE_EXECUTION


def test_non_finite_state_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="strain must be finite"):
        EpistemicState(strain=math.nan).normalized()
    with pytest.raises(ValueError, match="observability\[signal\] must be finite"):
        EpistemicState(observability={"signal": math.inf}).normalized()
    with pytest.raises(ValueError, match="hypotheses\[h1\] must be finite"):
        EpistemicState(hypotheses={"h1": math.inf}).normalized()
    with pytest.raises(ValueError, match="relevance\[signal\] must be non-negative"):
        EpistemicState(relevance={"signal": -1.0}).normalized()


def test_compute_strain_rejects_non_finite_lambda() -> None:
    with pytest.raises(ValueError, match="lam must be finite and non-negative"):
        compute_strain({"h1": 1.0}, {}, {}, lam=math.nan)
    with pytest.raises(ValueError, match="lam must be finite and non-negative"):
        compute_strain({"h1": 1.0}, {}, {}, lam=math.inf)
    with pytest.raises(ValueError, match="lam must be finite and non-negative"):
        compute_strain({"h1": 1.0}, {}, {}, lam=-1.0)


def test_compute_strain_rejects_invalid_observability_and_relevance() -> None:
    with pytest.raises(ValueError, match="observability\[signal\] must be finite"):
        compute_strain({"h1": 1.0, "h2": 1.0}, {"h1": {}, "h2": {}}, {"signal": math.nan})
    with pytest.raises(ValueError, match="observability\[signal\] must be finite"):
        compute_strain({"h1": 1.0, "h2": 1.0}, {"h1": {}, "h2": {}}, {"signal": math.inf})
    with pytest.raises(ValueError, match="relevance\[signal\] must be finite"):
        compute_strain({"h1": 1.0, "h2": 1.0}, {"h1": {}, "h2": {}}, {"signal": 1.0}, {"signal": math.inf})
    with pytest.raises(ValueError, match="relevance\[signal\] must be non-negative"):
        compute_strain({"h1": 1.0, "h2": 1.0}, {"h1": 1.0, "h2": 1.0}, {"signal": 1.0}, {"signal": -1.0})


def test_compute_strain_rejects_non_finite_numeric_predictions() -> None:
    with pytest.raises(ValueError, match="numeric predictions must be finite"):
        compute_strain({"h1": 0.5, "h2": 0.5}, {"h1": {"signal": math.nan}, "h2": {"signal": 1.0}}, {"signal": 1.0})
    with pytest.raises(ValueError, match="numeric predictions must be finite"):
        compute_strain({"h1": 0.5, "h2": 0.5}, {"h1": {"signal": 0.0}, "h2": {"signal": math.inf}}, {"signal": 1.0})


def test_compute_strain_rejects_non_finite_hypothesis_total() -> None:
    with pytest.raises(ValueError, match="hypotheses total must be finite"):
        compute_strain({"h1": 1e308, "h2": 1e308}, {}, {})


def test_policy_config_rejects_invalid_thresholds_and_bounds() -> None:
    with pytest.raises(ValueError, match="u_crit must be finite"):
        PolicyConfig(u_crit=math.nan)
    with pytest.raises(ValueError, match="calibration_crit must be finite"):
        PolicyConfig(calibration_crit=math.inf)
    with pytest.raises(ValueError, match="depth_bound must be positive"):
        PolicyConfig(depth_bound=0)
    with pytest.raises(ValueError, match="branch_bound must be positive"):
        PolicyConfig(branch_bound=0)


def test_policy_config_rejects_invalid_cost_weights() -> None:
    with pytest.raises(ValueError, match="cost_weights\[BLOCK\] must be finite"):
        PolicyConfig(cost_weights={Action.BLOCK: math.inf})
    with pytest.raises(ValueError, match="cost_weights\[BLOCK\] must be non-negative"):
        PolicyConfig(cost_weights={Action.BLOCK: -1.0})
