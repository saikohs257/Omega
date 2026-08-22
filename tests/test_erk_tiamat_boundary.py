from erk.fusion_assessment import assess_fusion
from erk.tiamat_bridge import to_tiamat_assessment
from oracle.fusion import EvidenceClaim, fuse_claims
from tiamat.engine import TiamatEngine
from tiamat.modes import TiamatMode
from tiamat.state import TiamatState


def _assessment(target: str):
    fusion = fuse_claims([EvidenceClaim("test", target, True, 0.9)])
    return assess_fusion(fusion)


def test_enter_assessment_is_observational() -> None:
    assessment = to_tiamat_assessment(_assessment("ENTER"))
    assert assessment.confidence >= 0.0
    assert assessment.uncertainty >= 0.0
    assert not hasattr(assessment, "approved")
    assert not hasattr(assessment, "transition")


def test_exit_assessment_is_observational() -> None:
    assessment = to_tiamat_assessment(_assessment("EXIT"))
    assert "disagreement" in assessment.evidence
    assert not hasattr(assessment, "approved")


def test_tiamat_transition_remains_explicit_state_operation() -> None:
    state = TiamatState.from_mapping({"mode": "QUIESCENT", "B": 0.0, "V": 0.0, "D": 0.0})
    next_state = TiamatEngine().step(state, {"V": 1.0})
    assert next_state.mode is TiamatMode.PRECURSOR
    assert next_state.mode.name == "PRECURSOR"
    assert next_state.mode.value == "P"
