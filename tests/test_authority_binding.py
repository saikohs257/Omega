from __future__ import annotations

import hashlib
import hmac
import pytest

from erk import Action
from erk.core import Authority, EpistemicState, EvidenceRecord, Transition, state_hash
from erk.kernel import AuthorityKey, ConstitutionalKernel, ConstitutionalViolation, KernelConfig

KEY = b"authority-test-key"
KEY_ID = "authority-test-key"
SOURCE = "trusted"
BRANCH = "test-branch"


def kernel() -> ConstitutionalKernel:
    return ConstitutionalKernel(
        KernelConfig(
            authority_keys={KEY_ID: AuthorityKey(KEY_ID, KEY, valid_from="2026-01-01T00:00:00Z", valid_until="2027-01-01T00:00:00Z")},
            branch_id=BRANCH,
        )
    )


def sign(record: EvidenceRecord, state: EpistemicState, k: ConstitutionalKernel | None = None) -> EvidenceRecord:
    k = k or kernel()
    signature = hmac.new(KEY, k._authority_binding(record, state), hashlib.sha256).hexdigest()
    return EvidenceRecord(record.evidence_id, record.source, record.timestamp, record.payload, record.authority_grant, signature, authority_grant_id=record.authority_grant_id)


def grant(state: EpistemicState, grant_id: str = "grant-1", **overrides: object) -> EvidenceRecord:
    k = kernel()
    payload = {
        "verified": True,
        "authority_key_id": KEY_ID,
        "authority_nonce": grant_id,
        "authority_expires_at": "2026-12-31T00:00:00Z",
        "authority_state_hash": state_hash(state),
        "authority_policy_hash": k._policy_hash(),
        "authority_branch_id": BRANCH,
        **overrides,
    }
    unsigned = EvidenceRecord("e", SOURCE, "2026-08-07T00:00:00Z", payload, authority_grant=1, authority_grant_id=grant_id)
    return sign(unsigned, state, k)


def test_valid_one_level_grant_is_admitted() -> None:
    state = EpistemicState()
    signed = grant(state)
    after = kernel().step(state, Action.BLOCK, (signed,))
    assert after.authority == Authority.SIMULATE
    assert after.used_authority_grants == ("grant-1",)


def test_grant_bound_to_state_hash_is_stale() -> None:
    state = EpistemicState()
    signed = grant(state)
    changed = EpistemicState(policy_version="different")
    with pytest.raises(ConstitutionalViolation, match="STALE_GRANT"):
        kernel().step(changed, Action.BLOCK, (signed,))


def test_grant_replay_is_rejected() -> None:
    state = EpistemicState()
    signed = grant(state)
    after = kernel().step(state, Action.BLOCK, (signed,))
    with pytest.raises(ConstitutionalViolation, match="GRANT_REPLAY"):
        kernel().step(after, Action.BLOCK, (signed,))


def test_grant_without_id_is_rejected() -> None:
    state = EpistemicState()
    unsigned = EvidenceRecord("e", SOURCE, "2026-08-07T00:00:00Z", {"authority_key_id": KEY_ID, "authority_nonce": ""}, authority_grant=1)
    signed = sign(unsigned, state)
    with pytest.raises(ConstitutionalViolation, match="GRANT_ID_MISSING"):
        kernel().step(state, Action.BLOCK, (signed,))


def test_cross_branch_grant_is_rejected() -> None:
    state = EpistemicState()
    signed = grant(state)
    other = ConstitutionalKernel(KernelConfig(
        authority_keys={KEY_ID: AuthorityKey(KEY_ID, KEY, valid_from="2026-01-01T00:00:00Z", valid_until="2027-01-01T00:00:00Z")},
        branch_id="other-branch",
    ))
    with pytest.raises(ConstitutionalViolation, match="BRANCH_MISMATCH"):
        other.step(state, Action.BLOCK, (signed,))


def test_unknown_key_is_rejected() -> None:
    state = EpistemicState()
    signed = grant(state)
    tampered = EvidenceRecord(signed.evidence_id, signed.source, signed.timestamp, {**dict(signed.payload), "authority_key_id": "substituted-key"}, signed.authority_grant, signed.authority_signature, authority_grant_id=signed.authority_grant_id)
    with pytest.raises(ConstitutionalViolation, match="UNKNOWN_KEY"):
        kernel().step(state, Action.BLOCK, (tampered,))


def test_expired_key_is_rejected() -> None:
    state = EpistemicState()
    k = ConstitutionalKernel(KernelConfig(
        authority_keys={KEY_ID: AuthorityKey(KEY_ID, KEY, valid_from="2026-01-01T00:00:00Z", valid_until="2026-08-01T00:00:00Z")},
        branch_id=BRANCH,
    ))
    signed = grant(state)
    with pytest.raises(ConstitutionalViolation, match="KEY_REVOKED_OR_OUT_OF_VALIDITY"):
        k.step(state, Action.BLOCK, (signed,))


def test_transition_cannot_escalate_without_kernel_authorization() -> None:
    state = EpistemicState()
    with pytest.raises(ValueError, match="kernel authorization"):
        Transition.apply(state, Action.BLOCK, authorized_authority=Authority.SIMULATE)
