from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .guards import GuardResult, evaluate_guards
from .state import TiamatMode, TiamatState


def transition(
    state: TiamatState,
    evidence: Mapping[str, Any],
    guard_results: tuple[GuardResult, ...] | None = None,
) -> TiamatState:
    """Pure deterministic TIAMAT transition.

    This is deliberately a conservative scaffold. Recovered empirical equations
    are admitted here only after independent replay/falsification tests.
    """
    guards = guard_results or evaluate_guards(state, evidence)
    triggered = {g.name for g in guards if g.triggered}

    if "DURATION_DAMAGE_HAZARD_GUARD" in triggered or "LATENT_HAZARD_PRECURSOR_GUARD" in triggered:
        return replace(state, mode=TiamatMode.HAZARD, promotion_count=state.promotion_count + 1)

    if "RELAXATION_WITH_RESIDUAL_DAMAGE" in triggered:
        return replace(state, mode=TiamatMode.HAZARD)

    if "COUPLED_TRANSFER_HAZARD_PROMOTION" in triggered:
        return replace(state, mode=TiamatMode.HAZARD, promotion_count=state.promotion_count + 1)

    if "EXCITATION_DURATION_EXPIRED" in triggered:
        return replace(state, mode=TiamatMode.RELAXING)

    if state.excitation > 0.0:
        return replace(state, mode=TiamatMode.EXCITED)

    return replace(state, mode=TiamatMode.IDLE)
