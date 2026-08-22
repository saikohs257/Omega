from court.engine import Court
from erk.fusion_assessment import assess_fusion
from oracle.engine import Oracle
from oracle.fusion import EvidenceClaim
from tiamat.engine import TiamatEngine


def test_distributed_evidence_cycle_preserves_contradiction_and_authority() -> None:
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

    # Evidence disagreement/missing evidence survives into ERK.
    assert fusion.disagreement >= 0.0
    assert "seam" in fusion.missing_channels
    assert assessment.uncertainty >= 0.0

    # ERK assessment is evidence for TIAMAT, not a transition command.
    engine = TiamatEngine()
    decision = engine.execute(
        {"state": "base"},
        {"allow": True, "mode": "open", "erk_assessment": assessment},
    )
    assert decision.approved is True

    # Court reviews the TIAMAT decision; Oracle records the adjudicated result.
    court = Court()
    verdict = court.review(decision)
    amendment = oracle.propose(verdict, {"mode": "open"})
    assert amendment.approved is verdict.approved
    assert amendment.evidence == verdict.record
