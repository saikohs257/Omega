from erk.fusion_assessment import assess_fusion
from oracle.fusion import EvidenceClaim, fuse_claims


def test_erk_preserves_disagreement_as_uncertainty() -> None:
    fusion = fuse_claims(
        [
            EvidenceClaim("chug", "RECOVERY", True, 0.9),
            EvidenceClaim("hinge", "RECOVERY", False, 0.8),
        ]
    )
    assessment = assess_fusion(fusion)
    assert assessment.disagreement > 0.0
    assert assessment.uncertainty > 0.0
    assert "DISAGREEMENT" in assessment.risk_flags


def test_erk_never_grants_authority() -> None:
    fusion = fuse_claims([EvidenceClaim("chug", "ENTER", True, 1.0)])
    assessment = assess_fusion(fusion)
    assert not hasattr(assessment, "approved")
    assert not hasattr(assessment, "authority")
    assert not hasattr(assessment, "transition")
