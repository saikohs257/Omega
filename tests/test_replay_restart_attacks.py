from __future__ import annotations

from erk.core import Action, EpistemicState, EvidenceRecord
from erk.grants import ConsumedGrantRegistry
from erk.replay import make_replay_record, verify_replay_chain


def _inputs():
    state = EpistemicState()
    evidence = (EvidenceRecord("e1", "test", "2026-08-07T00:00:00Z", {"verified": True}),)
    return state, evidence


def test_reconstructed_registry_preserves_replay_identity():
    state, evidence = _inputs()
    registry = ConsumedGrantRegistry(frozenset({"n1", "n2"}))
    reconstructed = ConsumedGrantRegistry(frozenset(sorted(registry.nonces)))
    a = make_replay_record(0, state, evidence, Action.BLOCK, registry)
    b = make_replay_record(0, state, evidence, Action.BLOCK, reconstructed)
    assert registry.digest() == reconstructed.digest()
    assert a.transition_hash == b.transition_hash


def test_dropped_registry_changes_replay_identity():
    state, evidence = _inputs()
    consumed = ConsumedGrantRegistry(frozenset({"n1"}))
    empty = ConsumedGrantRegistry()
    a = make_replay_record(0, state, evidence, Action.BLOCK, consumed)
    b = make_replay_record(0, state, evidence, Action.BLOCK, empty)
    assert a.registry_hash != b.registry_hash
    assert a.transition_hash != b.transition_hash


def test_restart_replay_chain_remains_verifiable():
    state, evidence = _inputs()
    registry = ConsumedGrantRegistry(frozenset({"n1"}))
    r0 = make_replay_record(0, state, evidence, Action.BLOCK, registry)
    r1 = make_replay_record(1, state, evidence, Action.BRANCH, registry, previous_hash=r0.transition_hash)
    serialized = (r0, r1)
    restored = tuple(serialized)
    assert verify_replay_chain(restored)


def test_chain_rejects_reordered_records():
    state, evidence = _inputs()
    registry = ConsumedGrantRegistry()
    r0 = make_replay_record(0, state, evidence, Action.BLOCK, registry)
    r1 = make_replay_record(1, state, evidence, Action.BRANCH, registry, previous_hash=r0.transition_hash)
    assert not verify_replay_chain((r1, r0))
