from __future__ import annotations

import pytest

from tiamat.reduction_shadow import (
    ReducedRecoveryState,
    ReducedState,
    incremental_information_gain,
    project_recovery_state,
    project_state,
    transition_mismatch,
)


def test_reduced_state_requires_d_and_v() -> None:
    state = project_state({"D": 0.7, "V": -0.1}, mode="RELAXATION", mode_age=12)
    assert state == ReducedState(0.7, -0.1, "RELAXATION", 12)


def test_recovery_augmented_model_keeps_recovery_separate_for_falsification() -> None:
    state = project_recovery_state(
        {"D": 0.7, "V": -0.1, "recovery": 0.4},
        mode="RELAXATION",
        mode_age=12,
    )
    assert state == ReducedRecoveryState(0.7, -0.1, "RELAXATION", 12, 0.4)


def test_transition_mismatch_is_alignment_based() -> None:
    assert transition_mismatch(("A", "B", "C"), ("A", "X", "C")) == pytest.approx(1 / 3)


def test_incremental_information_gain_is_positive_when_augmented_is_better() -> None:
    assert incremental_information_gain((0.4, 0.3), (0.2, 0.1)) == pytest.approx(0.2)
