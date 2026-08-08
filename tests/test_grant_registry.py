from __future__ import annotations

import hashlib
import pytest

from erk.core import Action, Authority, AuthorityGrant, EpistemicState, EvidenceRecord, Transition, state_hash
from erk.grants import ConsumedGrantRegistry, verify_and_consume_grant

SECRET = b"test-kernel-secret"


def make_grant(state: EpistemicState, evidence: tuple[EvidenceRecord, ...], nonce: str) -> AuthorityGrant:
    evidence_hash = hashlib.sha256(b"".join(e._canonical_content() for e in evidence)).hexdigest()
    unsigned = AuthorityGrant(state.authority, Authority.SIMULATE, evidence_hash, state_hash(state), state.policy_version, state.branch_id, nonce, "grant-" + nonce, "")
    signature = hashlib.sha256(SECRET + unsigned.message()).hexdigest()
    return AuthorityGrant(state.authority, Authority.SIMULATE, evidence_hash, state_hash(state), state.policy_version, state.branch_id, nonce, "grant-" + nonce, signature)


def test_grant_is_single_use() -> None:
    state = EpistemicState()
    evidence = (EvidenceRecord("e", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    grant = make_grant(state, evidence, "n1")
    registry = ConsumedGrantRegistry()
    _, registry = verify_and_consume_grant(grant, state, evidence, registry, SECRET)
    with pytest.raises(ValueError):
        verify_and_consume_grant(grant, state, evidence, registry, SECRET)


def test_registry_digest_is_deterministic() -> None:
    state = EpistemicState()
    evidence = (EvidenceRecord("e", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    grant = make_grant(state, evidence, "n1")
    _, a = verify_and_consume_grant(grant, state, evidence, ConsumedGrantRegistry(), SECRET)
    _, b = verify_and_consume_grant(grant, state, evidence, ConsumedGrantRegistry(), SECRET)
    assert a.digest() == b.digest()


def test_transition_without_grant_cannot_escalate() -> None:
    state = EpistemicState(authority=Authority.OBSERVE)
    evidence = (EvidenceRecord("e", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    next_state = Transition.apply(state, Action.BLOCK, evidence=evidence)
    assert next_state.authority == Authority.OBSERVE
