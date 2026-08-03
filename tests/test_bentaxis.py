from bentaxis.identity import Identity
from bentaxis.provenance import ProvenanceGraph
from bentaxis.store import BentAxisStore
from runtime.events import Event
from runtime.operators import AnnotateOperator
from runtime.workers import Worker


def test_store_chain_and_provenance_are_consistent() -> None:
    store = BentAxisStore()
    first = store.append(Event.create("alpha", {"i": 1}))
    second = store.append(Event.create("beta", {"i": 2}))

    assert first.identity != second.identity
    assert store.get(first.identity.digest) == first
    assert store.get(second.identity.digest) == second
    assert store.snapshot()["count"] == 2
    assert len(store.chain.links) == 2

    provenance = ProvenanceGraph()
    provenance.link(first.identity, second.identity, "derived_from")
    related = provenance.related_to(first.identity.digest)
    assert len(related) == 1
    assert related[0].relation == "derived_from"


def test_worker_emits_deterministic_trace() -> None:
    worker = Worker(worker_id="w1", operator=AnnotateOperator(name="mark", key="phase", value="alpha"))
    state, trace = worker.run({"seed": True})

    assert state["phase"] == "alpha"
    assert trace.worker_id == "w1"
    assert trace.operator == "mark"
    assert trace.after["phase"] == "alpha"
    assert len(worker.trajectory.events) == 1
    assert worker.trajectory.last().kind == "worker_run"
