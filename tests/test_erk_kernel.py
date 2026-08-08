from __future__ import annotations

import hashlib
import hmac
import pytest

from erk import (
    Action,
    Authority,
    ConstitutionalKernel,
    ConstitutionalViolation,
    EpistemicState,
    EvidenceRecord,
    KernelConfig,
)


def make_signed_grant(kernel: ConstitutionalKernel, state: EpistemicState, target: Authority) -> EvidenceRecord:
    unsigned = EvidenceRecord("e1", "authority", "t1", {"grant": int(target)}, authority_grant=target)
    signature = hmac.new(
        b"test-secret",
        kernel._authority_binding(unsigned, state),
        hashlib.sha256,
    ).hexdigest()
    return EvidenceRecord(
        "e1", "authority", "t1", {"grant": int(target)},
        authority_grant=target,
        authority_signature=signature,
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


def test_kernel_rejects_untrusted_authority_grant() -> None:
    kernel = ConstitutionalKernel()
    evidence = EvidenceRecord("e1", "attacker", "t1", {"grant": 2}, authority_grant=Authority.EXECUTE)
    with pytest.raises(ConstitutionalViolation):
        kernel.step(EpistemicState(), Action.BRANCH, (evidence,))


def test_kernel_rejects_forged_signature() -> None:
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={"authority": b"test-secret"}))
    evidence = EvidenceRecord(
        "e1", "authority", "t1", {"grant": 1},
        authority_grant=Authority.SIMULATE,
        authority_signature="0" * 64,
    )
    with pytest.raises(ConstitutionalViolation):
        kernel.step(EpistemicState(), Action.BRANCH, (evidence,))


def test_kernel_accepts_signed_authority_grant_one_level_at_a_time() -> None:
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={"authority": b"test-secret"}))
    state = EpistemicState()
    first_evidence = make_signed_grant(kernel, state, Authority.SIMULATE)
    first = kernel.step(state, Action.BRANCH, (first_evidence,))
    assert first.authority == Authority.SIMULATE

    second_evidence = make_signed_grant(kernel, first, Authority.EXECUTE)
    second = kernel.step(first, Action.BRANCH, (second_evidence,))
    assert second.authority == Authority.EXECUTE


def test_kernel_rejects_reuse_of_state_bound_grant() -> None:
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={"authority": b"test-secret"}))
    state = EpistemicState()
    evidence = make_signed_grant(kernel, state, Authority.SIMULATE)
    first = kernel.step(state, Action.BRANCH, (evidence,))
    with pytest.raises(ConstitutionalViolation):
        kernel.step(first, Action.BRANCH, (evidence,))


def test_kernel_replays_identically() -> None:
    kernel = ConstitutionalKernel()
    evidence = EvidenceRecord("e1", "trusted", "t1", {"x": 1})
    events = ((Action.BRANCH, (evidence,)),)
    first = kernel.replay(EpistemicState(), events)
    second = kernel.replay(EpistemicState(), events)
    assert first == second
    assert kernel.replay_hash(first) == kernel.replay_hash(second)


def test_kernel_rejects_cycle_even_with_execute_authority() -> None:
    from erk import GraphEdge, GraphNode, graph_metrics

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
