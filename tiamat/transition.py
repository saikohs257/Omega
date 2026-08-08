from dataclasses import replace
from typing import Any, Mapping
from .guards import GuardResult, evaluate_guards
from .state import TiamatMode, TiamatState

def _bounded(value: Any, current: float) -> float:
    if value is None: return current
    value = float(value)
    if not 0.0 <= value <= 1.0: raise ValueError("TIAMAT scalar evidence must be in [0, 1]")
    return value

def transition(state: TiamatState, evidence: Mapping[str, Any], guard_results: tuple[GuardResult, ...] | None = None) -> TiamatState:
    candidate = replace(state,
        excitation=_bounded(evidence.get("excitation"), state.excitation),
        damage=_bounded(evidence.get("damage"), state.damage),
        recovery=_bounded(evidence.get("recovery"), state.recovery),
        residual_load=_bounded(evidence.get("residual_load"), state.residual_load),
        momentum=_bounded(evidence.get("momentum"), state.momentum),
        mode_age_h=int(evidence.get("mode_age_h", state.mode_age_h + 1)),
        excitation_age_h=int(evidence.get("excitation_age_h", state.excitation_age_h + (1 if state.excitation > 0 else 0))),
        relaxation_age_h=int(evidence.get("relaxation_age_h", state.relaxation_age_h + (1 if state.mode is TiamatMode.RELAXING else 0))),
        refractory_age_h=int(evidence.get("refractory_age_h", state.refractory_age_h + 1)),
        promotion_count=max(0, int(evidence.get("promotion_count", state.promotion_count))),
        arrival_class=str(evidence.get("arrival_class", state.arrival_class)),
        hysteresis_memory=tuple(evidence.get("hysteresis_memory", state.hysteresis_memory)))
    guards = guard_results or evaluate_guards(candidate, evidence)
    triggered = {g.name for g in guards if g.triggered}
    if "DURATION_DAMAGE_HAZARD_GUARD" in triggered or "LATENT_HAZARD_PRECURSOR_GUARD" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD, promotion_count=candidate.promotion_count + 1, mode_age_h=0)
    if "RELAXATION_WITH_RESIDUAL_DAMAGE" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD, mode_age_h=0)
    if "COUPLED_TRANSFER_HAZARD_PROMOTION" in triggered:
        return replace(candidate, mode=TiamatMode.HAZARD, promotion_count=candidate.promotion_count + 1, mode_age_h=0)
    if "EXCITATION_DURATION_EXPIRED" in triggered:
        return replace(candidate, mode=TiamatMode.RELAXING, mode_age_h=0, relaxation_age_h=0)
    if candidate.excitation > 0.0:
        return replace(candidate, mode=TiamatMode.EXCITED, mode_age_h=0)
    return replace(candidate, mode=TiamatMode.IDLE, mode_age_h=0)
