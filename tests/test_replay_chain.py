from __future__ import annotations

from erk.core import Action, EpistemicState, EvidenceRecord
from erk.grants import ConsumedGrantRegistry
from erk.replay import make_replay_record, verify_replay_chain


def test_replay_chain_is_deterministic() -> None:
    state = EpistemicState()
    evidence = (EvidenceRecord("e1", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    registry = ConsumedGrantRegistry()
    a = make_replay_record(0, state, evidence, Action.BLOCK, registry)
    b = make_replay_record(0, state, evidence, Action.BLOCK, registry)
    assert a.transition_hash == b.transition_hash
    assert verify_replay_chain((a,))


def test_replay_chain_detects_tampering() -> None:
    state = EpistemicState()
    evidence = (EvidenceRecord("e1", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    record = make_replay_record(0, state, evidence, Action.BLOCK, ConsumedGrantRegistry())
    tampered = type(record)(record.sequence, record.state_hash, "tampered", record.policy_hash, record.branch_id, record.action, record.grant_id, record.registry_hash, record.previous_hash, record.transition_hash)
    assert not verify_replay_chain((tampered,))


def test_registry_change_changes_replay_identity() -> None:
    state = EpistemicState()
    evidence = (EvidenceRecord("e1", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    empty = ConsumedGrantRegistry()
    consumed = ConsumedGrantRegistry(frozenset({"nonce-1"}))
    a = make_replay_record(0, state, evidence, Action.BLOCK, empty)
    b = make_replay_record(0, state, evidence, Action.BLOCK, consumed)
    assert a.registry_hash != b.registry_hash
    assert a.transition_hash != b.transition_hash
