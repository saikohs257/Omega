from erk.core import (
    Action,
    Authority,
    EvidenceRecord,
    EpistemicState,
    GraphEdge,
    GraphNode,
    Supervisor,
    Transition,
    compute_strain,
    graph_metrics,
    state_hash,
)


def test_execution_requires_existing_execute_authority() -> None:
    supervisor = Supervisor()
    state = EpistemicState(authority=Authority.SIMULATE, strain=0.1)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(state)
    assert supervisor.supervise(state) != Action.ENABLE_EXECUTION


def test_execution_consumes_authority_and_cannot_self_escalate() -> None:
    state = EpistemicState(authority=Authority.EXECUTE, strain=0.1)
    next_state = Transition.apply(state, Action.ENABLE_EXECUTION)
    assert next_state.authority == Authority.SIMULATE

    state2 = EpistemicState(authority=Authority.SIMULATE, strain=0.1)
    next_state2 = Transition.apply(state2, Action.ENABLE_EXECUTION)
    assert next_state2.authority == Authority.SIMULATE


def test_authority_requires_separate_evidence_and_rises_one_level_at_a_time() -> None:
    evidence = EvidenceRecord(
        evidence_id="e1",
        source="test",
        timestamp="2026-01-01T00:00:00Z",
        payload={"supports": "execution"},
        authority_grant=2,
    )
    state = EpistemicState(authority=Authority.OBSERVE)
    once = Transition.apply(state, Action.BLOCK, [evidence])
    twice = Transition.apply(once, Action.BLOCK, [evidence])
    assert once.authority == Authority.SIMULATE
    assert twice.authority == Authority.EXECUTE


def test_evidence_is_immutable_and_hashed_from_content() -> None:
    record = EvidenceRecord("e1", "sensor", "t0", {"x": 1})
    assert len(record.provenance_hash) == 64
    try:
        record.payload["x"] = 2  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError("evidence payload must not be mutable")


def test_graph_cycles_are_detected_and_unsupported_depth_is_bounded() -> None:
    nodes = [
        GraphNode("a", "ASSUMPTION", supported=False),
        GraphNode("b", "INFERENCE"),
        GraphNode("c", "CONCLUSION"),
    ]
    edges = [
        GraphEdge("a", "b"),
        GraphEdge("b", "c"),
    ]
    metrics = graph_metrics(nodes, edges)
    assert metrics.unsupported_depth == 2
    assert metrics.critical_load["a"] == 2
    assert not metrics.cycles

    cyclic = graph_metrics(nodes, edges + [GraphEdge("c", "a")])
    assert cyclic.cycles


def test_strain_is_weighted_decision_relevant_disagreement() -> None:
    hypotheses = {"h1": 0.5, "h2": 0.5}
    predictions = {
        "h1": {"v": 0.0, "irrelevant": 0.0},
        "h2": {"v": 1.0, "irrelevant": 1.0},
    }
    low = compute_strain(hypotheses, predictions, {"v": 1.0, "irrelevant": 0.0})
    high = compute_strain(hypotheses, predictions, {"v": 1.0}, {"v": 1.0})
    assert low == high
    assert 0.0 < high < 1.0


def test_execution_is_blocked_by_strain_depth_or_calibration() -> None:
    supervisor = Supervisor()
    base = EpistemicState(authority=Authority.EXECUTE, strain=0.1)
    assert Action.ENABLE_EXECUTION in supervisor.safe_actions(base)
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(
        EpistemicState(authority=Authority.EXECUTE, strain=0.9)
    )
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(
        EpistemicState(authority=Authority.EXECUTE, strain=0.1, unsupported_depth=8)
    )
    assert Action.ENABLE_EXECUTION not in supervisor.safe_actions(
        EpistemicState(authority=Authority.EXECUTE, strain=0.1, calibration_error=0.25)
    )


def test_replay_state_hash_is_deterministic() -> None:
    state = EpistemicState(authority=Authority.SIMULATE, strain=0.2)
    assert state_hash(state) == state_hash(state)
