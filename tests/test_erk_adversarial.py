from __future__ import annotations

import pytest

from erk.core import (
    Action,
    Authority,
    EvidenceRecord,
    EpistemicState,
    GraphEdge,
    GraphNode,
    PolicyConfig,
    Supervisor,
    Transition,
    compute_strain,
    graph_metrics,
    state_hash,
)
from erk.kernel import ConstitutionalKernel, ConstitutionalViolation, KernelConfig


def signed_grant(kernel: ConstitutionalKernel, state: EpistemicState, target: Authority) -> EvidenceRecord:
    unsigned = EvidenceRecord("grant-1", "authority", "t1", {"decision": "grant"}, authority_grant=target)
    signature = __import__("hmac").new(
        b"test-secret",
        kernel._authority_binding(unsigned, state),
        __import__("hashlib").sha256,
    ).hexdigest()
    return EvidenceRecord(
        unsigned.evidence_id,
        unsigned.source,
        unsigned.timestamp,
        unsigned.payload,
        authority_grant=target,
        authority_signature=signature,
    )


def test_execution_cannot_self_grant_authority() -> None:
    state = EpistemicState(authority=Authority.SIMULATE)
    next_state = Transition.apply(state, Action.ENABLE_EXECUTION)
    assert next_state.authority == Authority.SIMULATE


def test_raw_evidence_cannot_grant_authority_inside_transition() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = EvidenceRecord("e1", "attacker", "t1", {"grant": 2}, authority_grant=Authority.EXECUTE)
    next_state = Transition.apply(state, Action.BRANCH, [evidence])
    assert next_state.authority == Authority.OBSERVE


def test_kernel_signed_grant_is_one_level_and_state_bound() -> None:
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={"authority": b"test-secret"}))
    state = EpistemicState()
    evidence = signed_grant(kernel, state, Authority.SIMULATE)
    first = kernel.step(state, Action.BRANCH, (evidence,))
    assert first.authority == Authority.SIMULATE
    with pytest.raises(ConstitutionalViolation):
        kernel.step(first, Action.BRANCH, (evidence,))


def test_tampered_provenance_is_rejected() -> None:
    with pytest.raises(ValueError):
        EvidenceRecord("e1", "source", "t1", {"x": 1}, provenance_hash="0" * 64)


def test_nested_evidence_payload_is_immutable() -> None:
    payload = {"nested": {"values": [1, 2]}}
    evidence = EvidenceRecord("e1", "source", "t1", payload)
    payload["nested"]["values"].append(3)
    assert list(evidence.payload["nested"]["values"]) == [1, 2]
    with pytest.raises(TypeError):
        evidence.payload["nested"]["values"] = (9,)


def test_epistemic_state_mappings_are_immutable() -> None:
    state = EpistemicState(observability={"x": 1.0}, hypotheses={"h": 1.0})
    with pytest.raises(TypeError):
        state.observability["x"] = 0.0
    with pytest.raises(TypeError):
        state.hypotheses["h"] = 0.0


def test_policy_config_is_immutable() -> None:
    config = PolicyConfig()
    with pytest.raises(TypeError):
        config.cost_weights[Action.BLOCK] = 999.0


def test_cycle_forces_non_execution_actions() -> None:
    nodes = [GraphNode("a", "x"), GraphNode("b", "x")]
    edges = [GraphEdge("a", "b"), GraphEdge("b", "a")]
    metrics = graph_metrics(nodes, edges)
    assert metrics.cycles
    state = EpistemicState(authority=Authority.EXECUTE, cycles=metrics.cycles)
    assert Action.ENABLE_EXECUTION not in Supervisor().safe_actions(state)


def test_strain_threshold_is_strict() -> None:
    state = EpistemicState(authority=Authority.EXECUTE, strain=0.80)
    assert Action.ENABLE_EXECUTION not in Supervisor().safe_actions(state)
    state = EpistemicState(authority=Authority.EXECUTE, strain=0.799999)
    assert Action.ENABLE_EXECUTION in Supervisor().safe_actions(state)


def test_depth_threshold_is_strict() -> None:
    state = EpistemicState(authority=Authority.EXECUTE, unsupported_depth=8)
    assert Action.ENABLE_EXECUTION not in Supervisor().safe_actions(state)
    state = EpistemicState(authority=Authority.EXECUTE, unsupported_depth=7)
    assert Action.ENABLE_EXECUTION in Supervisor().safe_actions(state)


def test_calibration_threshold_is_strict() -> None:
    state = EpistemicState(authority=Authority.EXECUTE, calibration_error=0.25)
    assert Action.ENABLE_EXECUTION not in Supervisor().safe_actions(state)
    state = EpistemicState(authority=Authority.EXECUTE, calibration_error=0.249999)
    assert Action.ENABLE_EXECUTION in Supervisor().safe_actions(state)


def test_branch_bound_is_inclusive() -> None:
    state = EpistemicState(authority=Authority.EXECUTE, active_branches=16)
    assert Action.ENABLE_EXECUTION in Supervisor().safe_actions(state)
    state = EpistemicState(authority=Authority.EXECUTE, active_branches=17)
    assert Action.ENABLE_EXECUTION not in Supervisor().safe_actions(state)


def test_strain_ignores_unobservable_disagreement() -> None:
    hypotheses = {"a": 0.5, "b": 0.5}
    predictions = {"a": {"x": 0.0}, "b": {"x": 1.0}}
    assert compute_strain(hypotheses, predictions, {"x": 0.0}) == 0.0


def test_strain_is_bounded() -> None:
    value = compute_strain(
        {"a": 0.5, "b": 0.5},
        {"a": {"x": 0.0}, "b": {"x": 1.0}},
        {"x": 1.0},
        lam=100.0,
    )
    assert 0.0 <= value <= 1.0


def test_replay_like_transition_is_deterministic() -> None:
    evidence = EvidenceRecord("e1", "court", "t1", {"x": 1})
    initial = EpistemicState()
    a = Transition.apply(initial, Action.BRANCH, [evidence])
    b = Transition.apply(initial, Action.BRANCH, [evidence])
    assert a == b
    assert state_hash(a) == state_hash(b)


def test_future_information_is_not_magically_present() -> None:
    state = EpistemicState(observability={"t0": 1.0})
    assert "t1" not in state.observability


def test_negative_authority_grant_cannot_reduce_or_corrupt_authority() -> None:
    state = EpistemicState(authority=Authority.SIMULATE)
    evidence = EvidenceRecord("e1", "bad-source", "t1", {}, authority_grant=-99)
    next_state = Transition.apply(state, Action.BRANCH, [evidence])
    assert next_state.authority == Authority.SIMULATE
