from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from bentaxis.hashchain import HashChain
from bentaxis.identity import Identity, to_canonical_bytes
from bentaxis.store import BentAxisStore
from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event
from runtime.replay import ReplayEngine
from runtime.state_vector import StateVector


def make_events() -> tuple[Event, ...]:
    return tuple(
        Event.create(
            kind,
            payload={"value": index},
            metadata={"source": "gate-a", "ordinal": index},
        )
        for index, kind in enumerate(("alpha", "beta", "gamma"))
    )


def make_records() -> tuple[ConstitutionalRecord, ...]:
    return tuple(
        ConstitutionalRecord(
            record_type=event.kind,
            payload=event.payload_dict(),
            previous_record=previous,
            timestamp=str(index),
        )
        for index, (event, previous) in enumerate(
            zip(make_events(), ("", "prev-alpha", "prev-beta"))
        )
    )


def test_canonical_bytes_and_identity_ignore_mapping_order() -> None:
    left = {"b": 2, "a": {"y": 4, "x": 3}}
    right = {"a": {"x": 3, "y": 4}, "b": 2}

    assert to_canonical_bytes(left) == to_canonical_bytes(right)
    assert Identity.calculate(left).digest == Identity.calculate(right).digest


def test_state_vector_is_immutable_and_updates_are_persistent() -> None:
    state = StateVector({"phase": "L0"})
    updated = state.with_updates(phase="L1", count=1)

    assert state.as_dict() == {"phase": "L0"}
    assert updated.as_dict() == {"phase": "L1", "count": 1}
    with pytest.raises(TypeError):
        state.values["phase"] = "mutated"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        state.values = {}  # type: ignore[misc]


def test_bentaxis_preserves_event_order_and_verifies_chain() -> None:
    events = make_events()
    store = BentAxisStore()
    stored = store.append_many(events)

    assert tuple(record.event for record in stored) == events
    assert [record.event.kind for record in store.events] == ["alpha", "beta", "gamma"]
    assert store.verify_integrity()
    assert store.chain.head == store.chain.links[-1]


def test_bentaxis_detects_tampered_chain() -> None:
    store = BentAxisStore()
    store.append_many(make_events())
    store._chain = HashChain(seed=store.chain.seed, links=store.chain.links[:-1] + ("tampered",))

    assert not store.verify_integrity()


def test_replay_equivalence_survives_fresh_engine_instances() -> None:
    records = make_records()

    results = [ReplayEngine().replay(records) for _ in range(20)]
    canonical_states = [result.state_vector.as_dict() for result in results]

    assert all(state == canonical_states[0] for state in canonical_states)
    assert canonical_states[0]["record_count"] == 3
    assert canonical_states[0]["last_record_type"] == "gamma"
    assert canonical_states[0]["last_payload"] == {"value": 2}


def test_replay_is_sensitive_to_order() -> None:
    records = make_records()
    forward = ReplayEngine().replay(records).state_vector.as_dict()
    reversed_state = ReplayEngine().replay(tuple(reversed(records))).state_vector.as_dict()

    assert forward != reversed_state
    assert forward["last_record_type"] == "gamma"
    assert reversed_state["last_record_type"] == "alpha"


def test_record_identity_changes_when_history_linkage_changes() -> None:
    record = ConstitutionalRecord(record_type="alpha", payload={"value": 1}, timestamp="1")
    linked = ConstitutionalRecord(
        record_type="alpha",
        payload={"value": 1},
        previous_record="prior",
        timestamp="1",
    )

    assert record.record_id != linked.record_id
