from court.engine import Court
from oracle.engine import Oracle
from runtime.events import Event
from runtime.trajectory import Trajectory
from tiamat.engine import TiamatEngine


def test_tiamat_can_approve_and_reject() -> None:
    engine = TiamatEngine()
    allow = engine.execute({"state": "base"}, {"allow": True, "mode": "open"})
    deny = engine.execute({"state": "base"}, {"allow": False, "mode": "closed"})
    assert allow.approved is True
    assert allow.state["mode"] == "Q"
    assert deny.approved is False
    assert deny.reason == "request disallowed"


def test_court_reviews_and_oracle_records_amendment() -> None:
    engine = TiamatEngine()
    court = Court()
    oracle = Oracle()
    decision = engine.execute({"state": "base"}, {"allow": True, "mode": "open"})
    verdict = court.review(decision)
    amendment = oracle.propose(verdict, {"mode": "open"})
    assert verdict.approved is True
    assert amendment.approved is True
    assert oracle.latest() == amendment
    assert court.records[-1]["approved"] is True


def test_tiamat_replay_reconstructs_seeded_state_and_trajectory() -> None:
    engine = TiamatEngine()
    trajectory = Trajectory().extend(
        (
            Event.create("alpha", {"value": 1}),
            Event.create("beta", {"value": 2}),
        )
    )

    replayed = engine.replay({"seed": "base"}, trajectory)

    assert replayed["seed"] == "base"
    assert replayed["record_count"] == 2
    assert replayed["last_record_type"] == "beta"
    assert replayed["last_payload"] == {"value": 2}
