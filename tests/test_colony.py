from colony.scheduler import ColonyScheduler
from runtime.operators import AnnotateOperator
from runtime.workers import Worker


def test_colony_scheduler_runs_workers_in_order() -> None:
    scheduler = ColonyScheduler(
        workers=[
            Worker(worker_id="w1", operator=AnnotateOperator(name="mark_a", key="a", value=1)),
            Worker(worker_id="w2", operator=AnnotateOperator(name="mark_b", key="b", value=2)),
        ]
    )
    result = scheduler.run_round({"seed": True})
    assert result.state["a"] == 1
    assert result.state["b"] == 2
    assert len(result.traces) == 2
    assert result.traces[0].worker_id == "w1"
    assert result.traces[1].worker_id == "w2"


def test_colony_scheduler_is_deterministic() -> None:
    scheduler = ColonyScheduler(
        workers=[
            Worker(worker_id="w1", operator=AnnotateOperator(name="mark", key="phase", value="alpha"))
        ]
    )
    left = scheduler.run_rounds({"seed": True}, rounds=3)
    right = scheduler.run_rounds({"seed": True}, rounds=3)
    assert left.state == right.state
    assert left.traces == right.traces
    assert left.state["phase"] == "alpha"
    assert len(left.traces) == 3
