"""Research-only reduced-state shadow model for TIAMAT.

This module deliberately does not replace the canonical state machine.  It
provides a small, auditable hypothesis for falsification experiments:
(D, V, q, tau_q), plus an optional recovery-augmented variant.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ReducedState:
    damage: float
    velocity: float
    mode: str
    mode_age: int

    def __post_init__(self) -> None:
        if not all(isfinite(float(x)) for x in (self.damage, self.velocity)):
            raise ValueError("damage and velocity must be finite")
        if self.mode_age < 0:
            raise ValueError("mode_age must be non-negative")


@dataclass(frozen=True, slots=True)
class ReducedRecoveryState(ReducedState):
    recovery: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isfinite(float(self.recovery)):
            raise ValueError("recovery must be finite")


def project_state(
    evidence: Mapping[str, object],
    *,
    mode: str = "UNKNOWN",
    mode_age: int = 0,
) -> ReducedState:
    """Project one evidence row into the minimal shadow state.

    ``velocity`` is read from canonical V when present; otherwise no derivative
    is silently fabricated.  Research callers must supply the observable they
    intend to test.
    """
    return ReducedState(
        damage=float(evidence["D"]),
        velocity=float(evidence["V"]),
        mode=mode,
        mode_age=mode_age,
    )


def project_recovery_state(
    evidence: Mapping[str, object],
    *,
    mode: str = "UNKNOWN",
    mode_age: int = 0,
) -> ReducedRecoveryState:
    """Optional augmented projection retaining recovery as a separate variable."""
    return ReducedRecoveryState(
        damage=float(evidence["D"]),
        velocity=float(evidence["V"]),
        mode=mode,
        mode_age=mode_age,
        recovery=float(evidence["recovery"]),
    )


def state_vector(state: ReducedState) -> tuple[float, float, int]:
    return (state.damage, state.velocity, state.mode_age)


def transition_mismatch(full_modes: Sequence[str], reduced_modes: Sequence[str]) -> float:
    """Fraction of aligned mode labels that disagree."""
    if len(full_modes) != len(reduced_modes):
        raise ValueError("mode sequences must be aligned and equal length")
    if not full_modes:
        return 0.0
    mismatches = sum(a != b for a, b in zip(full_modes, reduced_modes))
    return mismatches / len(full_modes)


def incremental_information_gain(
    baseline_errors: Sequence[float], augmented_errors: Sequence[float]
) -> float:
    """Mean baseline error minus mean augmented error.

    Positive values mean the augmented variables improve prediction; zero means
    no average gain.  This is a descriptive statistic, not a significance test.
    """
    if len(baseline_errors) != len(augmented_errors):
        raise ValueError("error sequences must be aligned")
    if not baseline_errors:
        return 0.0
    return sum(baseline_errors) / len(baseline_errors) - sum(augmented_errors) / len(augmented_errors)
