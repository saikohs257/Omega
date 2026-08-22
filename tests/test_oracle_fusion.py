from oracle import Oracle
from oracle.fusion import EvidenceClaim, fuse_claims


def test_fusion_preserves_disagreement_and_missing_channels() -> None:
    result = fuse_claims(
        [
            EvidenceClaim("chug", "RECOVERY", True, 0.9),
            EvidenceClaim("hinge", "RECOVERY", False, 0.8),
            EvidenceClaim("exit_latch", "EXIT", True, 0.7),
        ],
        expected_channels=("chug", "hinge", "seam", "exit_latch"),
    )

    assert len(result.claims) == 3
    assert result.disagreement > 0.0
    assert "RECOVERY" in result.contradictions
    assert result.missing_channels == ("seam",)
    assert result.confidence > 0.0


def test_oracle_exposes_fusion_without_authority() -> None:
    oracle = Oracle()
    result = oracle.fuse(
        [EvidenceClaim("chug", "ENTER", True, 1.0)]
    )

    assert result.claims[0].target_phase == "ENTER"
    assert not hasattr(result, "approved")
    assert not hasattr(result, "transition")


def test_agreement_is_explicit_when_claims_match() -> None:
    result = fuse_claims(
        [
            EvidenceClaim("a", "ENTER", True, 0.8),
            EvidenceClaim("b", "ENTER", True, 0.9),
        ]
    )

    assert result.agreement == 1.0
    assert result.disagreement == 0.0
    assert result.contradictions == ()
