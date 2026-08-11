from __future__ import annotations

from tiamat.reduction_shadow import incremental_information_gain, project_recovery_state, project_state


def test_reduction_projection_does_not_invent_velocity() -> None:
    state = project_state({"D": 0.5, "V": 0.0}, mode="QUIESCENT")
    assert state.velocity == 0.0


def test_recovery_identity_is_testable_not_enforced() -> None:
    state = project_recovery_state(
        {"D": 0.8, "V": 0.1, "recovery": 0.7},
        mode="EXCITATION",
    )
    # A counterexample may legally specify increasing D/V alongside positive
    # recovery; the research model must not algebraically forbid the observation.
    assert state.recovery == 0.7
    assert state.velocity == 0.1


def test_zero_information_gain_is_neutral() -> None:
    assert incremental_information_gain((0.2, 0.4), (0.2, 0.4)) == 0.0
