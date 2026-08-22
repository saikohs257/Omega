from erk.fusion_assessment import assess_fusion
from erk.tiamat_bridge import to_tiamat_assessment
from oracle.fusion import EvidenceClaim, fuse_claims


def test_erk_to_tiamat_is_evidence_only() -> None:
    fusion = fuse_claims([EvidenceClaim("chug", "RECOVERY", True, 0.9)])
    assessment = assess_fusion(fusion)
    bridged = to_tiamat_assessment(assessment)

    assert bridged.confidence == assessment.confidence
    assert bridged.uncertainty == assessment.uncertainty
    assert bridged.evidence["disagreement"] == assessment.disagreement
    assert not hasattr(bridged, "transition")
    assert not hasattr(bridged, "state")
    assert not hasattr(bridged, "authority")
