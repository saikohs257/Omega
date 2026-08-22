from dic import DIC, SidecarEvidence
from oracle.engine import Oracle


def test_dic_to_oracle_preserves_distributed_evidence() -> None:
    dic = DIC()
    dic.emit(SidecarEvidence("chug", "RECOVERY", True, 0.9))
    dic.emit(SidecarEvidence("hinge", "PRESSURE", True, 0.8))
    dic.emit(SidecarEvidence("exit_latch", "EXIT", True, 0.7))

    fused = Oracle().fuse(
        dic.to_oracle_claims(),
        expected_channels=("chug", "hinge", "seam", "exit_latch"),
    )

    assert len(fused.claims) == 3
    assert fused.missing_channels == ("seam",)
    assert set(fused.phases) == {"RECOVERY", "PRESSURE", "EXIT"}
    assert fused.disagreement == 0.0
    assert not hasattr(fused, "approved")
    assert not hasattr(fused, "transition")
