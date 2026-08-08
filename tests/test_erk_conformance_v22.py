from __future__ import annotations

import math

from erk.core import Action, Authority, EpistemicState, GraphEdge, GraphNode, PolicyConfig, Supervisor, compute_strain, graph_metrics


def test_strain_is_bounded() -> None:
    state = EpistemicState(
        hypotheses={"h1": 0.5, "h2": 0.5},
        predictions={"h1": {"v": 0}, "h2": {"v": 1}},
        observability={"v": 1.0},
    )
    u = compute_strain(state.hypotheses, state.predictions, state.observability)
    assert 0.0 <= u < 1.0
    assert math.isfinite(u)


def test_graph_cycle_is_detected_without_mutating_topology() -> None:
    nodes = (GraphNode("a", "ASSUMPTION", False), GraphNode("b", "INFERENCE"))
    edges = (GraphEdge("a", "b"), GraphEdge("b", "a"))
    metrics = graph_metrics(nodes, edges)
    assert metrics.cycles
    assert metrics.unsupported_depth >= 1


def test_execution_is_impossible_below_execute_authority() -> None:
    supervisor = Supervisor(PolicyConfig())
    state = EpistemicState(authority=Authority.SIMULATE)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(state)


def test_execution_requires_all_runtime_safety_bounds() -> None:
    supervisor = Supervisor(PolicyConfig(u_crit=0.8, depth_bound=8, calibration_crit=0.25, branch_bound=16))
    state = EpistemicState(authority=Authority.EXECUTE, strain=0.8)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(state)

    state = EpistemicState(authority=Authority.EXECUTE, strain=0.1, unsupported_depth=8)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(state)

    state = EpistemicState(authority=Authority.EXECUTE, strain=0.1, calibration_error=0.25)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(state)


def test_terminal_state_has_no_actions() -> None:
    supervisor = Supervisor()
    state = EpistemicState(terminal="REJECTED")
    assert supervisor.safe_actions(state) == ()
    assert supervisor.supervise(state) == Action.ESCALATE
