from bentaxis.capsule import BentAxisCapsule
from bentaxis.store import BentAxisStore
from court.engine import Court
from oracle.engine import Oracle
from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event
from runtime.replay import ReplayEngine
from tiamat import TiamatMode, TiamatState
from tiamat.engine import TiamatEngine


def test_integrated_pipeline_uses_canonical_tiamat_transitions() -> None:
    """The canonical integration path must exercise TIAMAT structural state."""
    store = BentAxisStore()
    records = []
    evidence = (("forcing", {"V": 0.1}), ("excitation", {"V": 0.1, "B": 0.2}))
    for index, (kind, payload) in enumerate(evidence):
        event = Event.create(kind, payload)
        store.append(event)
        records.append(
            ConstitutionalRecord(
                record_type=kind,
                payload=event.payload_dict(),
                timestamp=str(index),
            )
        )

    capsule = BentAxisCapsule.from_store(store)
    replay = ReplayEngine().replay(tuple(records))

    engine = TiamatEngine()
    initial = TiamatState()
    live = initial
    for item in ({"V": 0.1}, {"V": 0.1, "B": 0.2}):
        live = engine.transition_state(live, item)

    assert live.mode is TiamatMode.EXCITATION
    assert engine.replay_state(initial, ({"V": 0.1}, {"V": 0.1, "B": 0.2})) == live

    decision = engine.execute(live.to_dict(), {"structural_state": live.to_dict()})
    verdict = Court().review(decision)
    amendment = Oracle().propose(verdict, {"mode": live.mode.value})

    assert capsule.manifest["count"] == 2
    assert replay.state_vector.get("record_count") == 2
    assert decision.approved is True
    assert verdict.approved is True
    assert amendment.approved is True
