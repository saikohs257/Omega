from bentaxis.capsule import BentAxisCapsule
from bentaxis.store import BentAxisStore
from runtime.constitutional_record import ConstitutionalRecord
from runtime.replay import ReplayEngine
from runtime.events import Event
from runtime.state_vector import StateVector
import pytest


def test_replay_is_deterministic() -> None:
    records = tuple(
        ConstitutionalRecord(
            record_type=event.kind,
            payload=event.payload_dict(),
            timestamp=str(index),
        )
        for index, event in enumerate(
            (
                Event.create("alpha", {"i": 1}),
                Event.create("beta", {"i": 2}),
                Event.create("gamma", {"i": 3}),
            )
        )
    )

    engine = ReplayEngine()
    result_a = engine.replay(records)
    result_b = engine.replay(records)

    assert result_a.records == result_b.records
    assert result_a.state_vector.as_dict() == result_b.state_vector.as_dict()
    assert result_a.state_vector.get("record_count") == 3
    assert result_a.state_vector.get("last_record_type") == "gamma"
    assert result_a.state_vector.get("last_payload") == {"i": 3}


def test_registered_operator_controls_reconstruction() -> None:
    class MarkerOperator:
        def reconstruct(self, record: ConstitutionalRecord, state):
            return state.with_updates(marker=record.payload["marker"])

    engine = ReplayEngine()
    engine.registry.register("marker", MarkerOperator())
    record = ConstitutionalRecord(
        record_type="marker",
        payload={"marker": "custom"},
        timestamp="1",
    )

    result = engine.replay((record,))

    assert result.state_vector.get("marker") == "custom"
    assert result.state_vector.get("record_count") is None


def test_replay_preserves_explicit_initial_state() -> None:
    record = ConstitutionalRecord(record_type="alpha", payload={"i": 1}, timestamp="1")
    initial = StateVector({"seed": "base"})

    result = ReplayEngine().replay((record,), initial_state=initial)

    assert result.state_vector.get("seed") == "base"
    assert result.state_vector.get("record_count") == 1


def test_replay_rejects_invalid_boundary_inputs() -> None:
    engine = ReplayEngine()
    record = ConstitutionalRecord(record_type="alpha", payload={}, timestamp="1")

    with pytest.raises(TypeError, match="initial_state"):
        engine.replay((record,), initial_state={})

    with pytest.raises(TypeError, match="records"):
        engine.replay((record, object()))


def test_capsule_round_trip_is_stable() -> None:
    store = BentAxisStore()
    store.append(Event.create("alpha", {"i": 1}))
    store.append(Event.create("beta", {"i": 2}))
    capsule = BentAxisCapsule.from_store(store)
    assert capsule.manifest["count"] == 2
    assert capsule.manifest["chain_head"] == store.chain.head
    assert capsule.canonical_hash() == BentAxisCapsule.from_store(store).canonical_hash()
