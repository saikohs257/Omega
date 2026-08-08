from bentaxis.capsule import BentAxisCapsule
from bentaxis.store import BentAxisStore
from runtime.events import Event
from runtime.replay import ReplayEngine
from runtime.trajectory import Trajectory


def test_replay_is_deterministic() -> None:
    events = (
        Event.create("alpha", {"i": 1}),
        Event.create("beta", {"i": 2}),
        Event.create("gamma", {"i": 3}),
    )
    trajectory = Trajectory().extend(events)
    engine = ReplayEngine()
    result_a = engine.replay({"seed": True}, trajectory)
    result_b = engine.replay({"seed": True}, trajectory)
    assert result_a.state == result_b.state
    assert result_a.trajectory == result_b.trajectory
    assert result_a.state["event_count"] == 3
    assert result_a.state["last_event_kind"] == "gamma"


def test_capsule_round_trip_is_stable() -> None:
    store = BentAxisStore()
    store.append(Event.create("alpha", {"i": 1}))
    store.append(Event.create("beta", {"i": 2}))
    capsule = BentAxisCapsule.from_store(store)
    assert capsule.manifest["count"] == 2
    assert capsule.manifest["chain_head"] == store.chain.head
    assert capsule.canonical_hash() == BentAxisCapsule.from_store(store).canonical_hash()
