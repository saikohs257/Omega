from court.engine import Court
from erk.fusion_assessment import assess_fusion
from oracle.engine import Oracle
from oracle.fusion import EvidenceClaim
from tiamat.engine import TiamatEngine
from tiamat.state import TiamatState


def test_real_state_oracle_erk_tiamat_court_path_preserves_state_and_authority() -> None:
    oracle = Oracle()
    claims = [
        EvidenceClaim("chug", "RECOVERY", True, 0.90),
        EvidenceClaim("hinge", "PRESSURE", True, 0.85),
        EvidenceClaim("exit_latch", "EXIT", True, 0.80),
    ]
    fusion = oracle.fuse(
        claims,
        expected_channels=("chug", "hinge", "seam", "exit_latch"),
    )
    assessment = assess_fusion(fusion)

    initial = TiamatState.from_mapping({"mode": "QUIESCENT", "B": 0.0, "V": 0.0, "D": 0.0})
    engine = TiamatEngine()
    decision = engine.execute(
        initial.to_dict(),
        {"V": 1.0, "erk_assessment": assessment},
    )

    assert decision.approved is True
    assert decision.state["mode"] == "P"
    assert "erk_assessment" not in decision.state
    assert decision.event.kind == "tiamat_transition"

    court = Court()
    verdict = court.review(decision)
    amendment = oracle.propose(verdict, {"mode": decision.state["mode"]})

    assert verdict.approved is True
    assert amendment.approved is True
    assert amendment.evidence == verdict.record
    assert oracle.latest() == amendment
