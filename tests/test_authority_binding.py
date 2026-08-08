from __future__ import annotations

import hashlib
import hmac
import pytest

from erk.core import Authority, EpistemicState, EvidenceRecord, Transition
from erk.kernel import ConstitutionalKernel, ConstitutionalViolation, KernelConfig

KEY = b"authority-test-key"
SOURCE = "trusted"


def sign(record: EvidenceRecord, state: EpistemicState) -> EvidenceRecord:
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={SOURCE: KEY}))
    signature = hmac.new(KEY, kernel._authority_binding(record, state), hashlib.sha256).hexdigest()
    return EvidenceRecord(record.evidence_id, record.source, record.timestamp, record.payload, record.authority_grant, signature)


def test_valid_one_level_grant_is_admitted() -> None:
    state = EpistemicState()
    unsigned = EvidenceRecord("e", SOURCE, "2026-08-07T00:00:00Z", {"verified": True}, authority_grant=1)
    signed = sign(unsigned, state)
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={SOURCE: KEY}))
    after = kernel.step(state, __import__("erk").Action.BLOCK, (signed,))
    assert after.authority == Authority.SIMULATE


def test_grant_bound_to_state_hash() -> None:
    state = EpistemicState()
    unsigned = EvidenceRecord("e", SOURCE, "2026-08-07T00:00:00Z", {"verified": True}, authority_grant=1)
    signed = sign(unsigned, state)
    changed = EpistemicState(policy_version="different")
    kernel = ConstitutionalKernel(KernelConfig(authority_keys={SOURCE: KEY}))
    with pytest.raises(ConstitutionalViolation):
        kernel.step(changed, __import__("erk").Action.BLOCK, (signed,))


def test_transition_cannot_escalate_without_kernel_authorization() -> None:
    state = EpistemicState()
    with pytest.raises(ValueError):
        Transition.apply(state, __import__("erk").Action.BLOCK, authorized_authority=Authority.SIMULATE)
