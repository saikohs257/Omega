from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .guards import GuardResult, evaluate_guards
from .state import TiamatMode, TiamatState


def _bounded(value: Any, current: float) -> float:
    if value is None:
        return current
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError("TIAMAT scalar evidence must be in [0, 1]")
    return value


def transition(
    state: TiamatState,
    evidence: Mapping[str, Any],
    guard_results: tuple[GuardResult, ...] | None = None,
) -> TiamatState:
    """Pure deterministic TIAMAT transition.

    Evidence fields explicitly represented by the state are applied first;
    guards are then evaluated against that candidate state. This same function
    is the live and replay transition boundary.
    """
    timers = dict(state.timers)
    timers["excitation_age"] = int(timers.get("excitation_age", 0)) + 1
    candidate = replace(
        state,
        damage=_bounded(evidence.get("damage"), state.damage),
        recovery=_bounded(evidence.get("recovery"), state.recovery),
        residual_load=_bounded(evidence.get("residual_load"), state.residual_load),
        excitation=_bounded(evidence.get("excitation"), state.excitation),
        refractory=max(0, int(evidence.get("refractory", state.refractory))),
        promotion_count=max(0, int(evidence.get("promotion_count", state.promotion_count))),
        timers=timers,
    )
    guards = guard_results or evaluate_guards(candidate, evidence)
    triggered = {g.name for g in guards if g.triggered}

    if "DURATION_DAMAGE_HAZARD_GUARD" in triggered or "LATENT_HAZARD_PRECURSOR_GUARD" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD, promotion_count=candidate.promotion_count + 1)

    if "RELAXATION_WITH_RESIDUAL_DAMAGE" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD)

    if "COUPLED_TRANSFER_HAZARD_PROMOTION" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD, promotion_count=candidate.promotion_count + 1)

    if "EXCITATION_DURATION_EXPIRED" in triggered:
        return replace(candidate, mode=TiamatMode.RELAXING)

    if candidate.excitation > 0.0:
        return replace(candidate, mode=TiamatMode.EXCITED)

    return replace(candidate, mode=TiamatMode.IDLE)
