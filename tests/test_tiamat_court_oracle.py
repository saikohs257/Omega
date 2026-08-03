from court.engine import Court
from oracle.engine import Oracle
from tiamat.engine import TiamatEngine


def test_tiamat_can_approve_and_reject() -> None:
    engine = TiamatEngine()
    allow = engine.execute({"state": "base"}, {"allow": True, "mode": "open"})
    deny = engine.execute({"state": "base"}, {"allow": False, "mode": "closed"})
    assert allow.approved is True
    assert allow.state["mode"] == "open"
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
