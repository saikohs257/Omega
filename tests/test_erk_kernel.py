from __future__ import annotations

import pytest

from erk import (
    Action,
    Authority,
    ConstitutionalKernel,
    ConstitutionalViolation,
    EpistemicState,
    EvidenceRecord,
)


def test_kernel_rejects_execution_without_execute_authority() -> None:
    kernel = ConstitutionalKernel()
    with pytest.raises(ConstitutionalViolation):
        kernel.step(EpistemicState(authority=Authority.SIMULATE), Action.ENABLE_EXECUTION)


def test_kernel_consumes_execute_authority() -> None:
    kernel = ConstitutionalKernel()
    state = EpistemicState(authority=Authority.EXECUTE)
    next_state = kernel.step(state, Action.ENABLE_EXECUTION)
    assert next_state.authority == Authority.SIMULATE


def test_kernel_replays_identically() -> None:
    kernel = ConstitutionalKernel()
    evidence = EvidenceRecord("e1", "trusted", "t1", {"x": 1})
    events = ((Action.BRANCH, (evidence,)),)
    first = kernel.replay(EpistemicState(), events)
    second = kernel.replay(EpistemicState(), events)
    assert first == second
    assert kernel.replay_hash(first) == kernel.replay_hash(second)


def test_kernel_rejects_cycle_even_with_execute_authority() -> None:
    from erk import GraphEdge, GraphNode, Supervisor, graph_metrics

    nodes = [GraphNode("a", "inference"), GraphNode("b", "inference")]
    metrics = graph_metrics(nodes, [GraphEdge("a", "b"), GraphEdge("b", "a")])
    state = EpistemicState(authority=Authority.EXECUTE, cycles=metrics.cycles)
    kernel = ConstitutionalKernel()
    with pytest.raises(ConstitutionalViolation):
        kernel.step(state, Action.ENABLE_EXECUTION)


def test_kernel_preserves_evidence_count_monotonicity() -> None:
    kernel = ConstitutionalKernel()
    state = EpistemicState()
    evidence = EvidenceRecord("e1", "trusted", "t1", {"x": 1})
    next_state = kernel.step(state, Action.BRANCH, (evidence,))
    assert next_state.evidence_count == state.evidence_count + 1
