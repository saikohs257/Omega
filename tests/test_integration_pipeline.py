from atlas.hypercube import HypercubeAtlas
from bentaxis.capsule import BentAxisCapsule
from bentaxis.store import BentAxisStore
from colony.scheduler import ColonyScheduler
from court.engine import Court
from hypergraph.engine import Hypergraph
from oracle.engine import Oracle
from runtime.events import Event
from runtime.operators import AnnotateOperator
from runtime.replay import ReplayEngine
from runtime.trajectory import Trajectory
from runtime.workers import Worker
from sheaf.compat import LocalSection, Sheaf
from simplicial.complex import SimplicialComplex
from tiamat.engine import TiamatEngine


def test_end_to_end_pipeline_is_stable() -> None:
    store = BentAxisStore()
    trajectory = Trajectory()
    for kind, value in [("alpha", 1), ("beta", 2), ("gamma", 3)]:
        event = Event.create(kind, {"value": value})
        store.append(event)
        trajectory = trajectory.append(event)

    capsule = BentAxisCapsule.from_store(store)
    replay = ReplayEngine().replay({"seed": True}, trajectory)
    worker = Worker(worker_id="w1", operator=AnnotateOperator(name="tag", key="phase", value="alpha"))
    colony = ColonyScheduler(workers=[worker])
    colony_result = colony.run_round(replay.state)

    atlas = HypercubeAtlas(dimensions=4)
    coordinate = atlas.project({"axis_0": 1, "axis_2": 1})
    chart = atlas.local_chart(coordinate)

    hypergraph = Hypergraph()
    hypergraph.add(["a", "b", "c"], "concept", {"weight": 3})

    simplicial = SimplicialComplex()
    simplicial.add(["a", "b", "c"], {"kind": "concept"})

    sheaf = Sheaf()
    sheaf.add(LocalSection.create("market", {"state": "calm"}))
    sheaf.add(LocalSection.create("market", {"state": "calm", "extra": True}))

    tiamat = TiamatEngine()
    decision = tiamat.execute(colony_result.state, {"allow": True, "mode": "open"})
    court = Court()
    verdict = court.review(decision)
    oracle = Oracle()
    amendment = oracle.propose(verdict, {"mode": "open"})

    assert capsule.manifest["count"] == 3
    assert replay.state["event_count"] == 3
    assert colony_result.state["phase"] == "alpha"
    assert chart.origin == coordinate
    assert hypergraph.relation_count() == 1
    assert simplicial.contains(["a", "b", "c"])
    assert sheaf.compatibility() is True
    assert decision.approved is True
    assert verdict.approved is True
    assert amendment.approved is True
    assert oracle.latest() == amendment
