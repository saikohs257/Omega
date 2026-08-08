from __future__ import annotations

import hashlib
import pytest

from erk.core import Action, Authority, AuthorityGrant, EpistemicState, EvidenceRecord, Transition, state_hash

SECRET = b"test-kernel-secret"


def grant_for(state: EpistemicState, evidence: tuple[EvidenceRecord, ...], target: Authority, grant_id: str = "g1") -> AuthorityGrant:
    evidence_hash = hashlib.sha256(b"".join(e._canonical_content() for e in evidence)).hexdigest()
    unsigned = AuthorityGrant(state.authority, target, evidence_hash, state_hash(state), state.policy_version, grant_id, "")
    signature = hashlib.sha256(SECRET + unsigned.message()).hexdigest()
    return AuthorityGrant(state.authority, target, evidence_hash, state_hash(state), state.policy_version, grant_id, signature)


def test_transition_rejects_unverified_two_level_grant() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    grant = AuthorityGrant(Authority.OBSERVE, Authority.EXECUTE, "", state_hash(state), state.policy_version, "g1", "bad")
    with pytest.raises(ValueError):
        Transition.apply(state, Action.BLOCK, grant=grant, kernel_secret=SECRET)


def test_transition_allows_only_one_verified_level() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = (EvidenceRecord("e1", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    grant = grant_for(state, evidence, Authority.SIMULATE)
    next_state = Transition.apply(state, Action.BLOCK, evidence=evidence, grant=grant, kernel_secret=SECRET)
    assert next_state.authority == Authority.SIMULATE


def test_simulate_to_execute_requires_distinct_verified_grant() -> None:
    state = EpistemicState(authority=Authority.SIMULATE, evidence_count=1)
    evidence = (EvidenceRecord("e2", "test", "2026-08-07T00:00:01Z", {"verified": True}),)
    grant = grant_for(state, evidence, Authority.EXECUTE, "g2")
    next_state = Transition.apply(state, Action.BLOCK, evidence=evidence, grant=grant, kernel_secret=SECRET)
    assert next_state.authority == Authority.EXECUTE


def test_grant_replay_against_changed_state_is_rejected() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = (EvidenceRecord("e3", "test", "2026-08-07T00:00:02Z", {"x": 1}),)
    grant = grant_for(state, evidence, Authority.SIMULATE)
    changed = EpistemicState(authority=Authority.OBSERVE, evidence_count=1)
    with pytest.raises(ValueError):
        Transition.apply(changed, Action.BLOCK, evidence=evidence, grant=grant, kernel_secret=SECRET)


def test_forged_signature_is_rejected() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = (EvidenceRecord("e4", "test", "2026-08-07T00:00:03Z", {"x": 2}),)
    grant = grant_for(state, evidence, Authority.SIMULATE)
    forged = AuthorityGrant(grant.prior, grant.target, grant.evidence_hash, grant.state_hash, grant.policy_hash, grant.grant_id, "forged")
    with pytest.raises(ValueError):
        Transition.apply(state, Action.BLOCK, evidence=evidence, grant=forged, kernel_secret=SECRET)


def test_enable_execution_consumes_execute_authority() -> None:
    state = EpistemicState(authority=Authority.EXECUTE)
    next_state = Transition.apply(state, Action.ENABLE_EXECUTION)
    assert next_state.authority == Authority.SIMULATE


def test_evidence_alone_cannot_escalate_authority() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = (EvidenceRecord("e5", "test", "2026-08-07T00:00:04Z", {"authority_grant": 2}),)
    next_state = Transition.apply(state, Action.BLOCK, evidence=evidence)
    assert next_state.authority == Authority.OBSERVE
    assert next_state.evidence_count == 1


def test_transition_is_deterministic() -> None:
    state = EpistemicState(authority=Authority.SIMULATE, evidence_count=2)
    evidence = (EvidenceRecord("e6", "test", "2026-08-07T00:00:05Z", {"x": 3}),)
    a = Transition.apply(state, Action.BLOCK, evidence=evidence)
    b = Transition.apply(state, Action.BLOCK, evidence=evidence)
    assert a == b
