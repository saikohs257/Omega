from __future__ import annotations

import pytest

from erk.core import Action, Authority, EpistemicState, EvidenceRecord, Transition


def test_transition_cannot_jump_observe_to_execute_via_authorized_argument() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    with pytest.raises(ValueError):
        Transition.apply(state, Action.BLOCK, authorized_authority=Authority.EXECUTE)


def test_transition_allows_only_one_level_authority_grant() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    next_state = Transition.apply(state, Action.BLOCK, authorized_authority=Authority.SIMULATE)
    assert next_state.authority == Authority.SIMULATE


def test_transition_cannot_grant_execute_without_verified_kernel_boundary() -> None:
    state = EpistemicState(authority=Authority.SIMULATE)
    with pytest.raises(ValueError):
        Transition.apply(state, Action.BLOCK, authorized_authority=Authority.EXECUTE)


def test_enable_execution_never_leaves_authority_at_execute() -> None:
    state = EpistemicState(authority=Authority.EXECUTE)
    next_state = Transition.apply(state, Action.ENABLE_EXECUTION)
    assert next_state.authority == Authority.SIMULATE


def test_evidence_is_counted_but_cannot_by_itself_escalate_authority() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = EvidenceRecord(
        evidence_id="e1",
        source="test",
        timestamp="2026-08-07T00:00:00Z",
        payload={"verified": True},
    )
    next_state = Transition.apply(state, Action.BLOCK, evidence=(evidence,))
    assert next_state.evidence_count == 1
    assert next_state.authority == Authority.OBSERVE


def test_transition_is_deterministic() -> None:
    state = EpistemicState(authority=Authority.SIMULATE, evidence_count=2)
    evidence = EvidenceRecord(
        evidence_id="e2",
        source="test",
        timestamp="2026-08-07T00:00:01Z",
        payload={"x": 1},
    )
    a = Transition.apply(state, Action.BLOCK, evidence=(evidence,))
    b = Transition.apply(state, Action.BLOCK, evidence=(evidence,))
    assert a == b


def test_forbidden_two_level_grant_is_rejected_from_every_starting_level() -> None:
    for starting in (Authority.OBSERVE, Authority.SIMULATE):
        state = EpistemicState(authority=starting)
        with pytest.raises(ValueError):
            Transition.apply(state, Action.BLOCK, authorized_authority=Authority.EXECUTE)
