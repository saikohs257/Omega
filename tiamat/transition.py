from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .guards import GuardResult, evaluate_guards
from .state import TiamatMode, TiamatState


def _apply_measurements(state: TiamatState, evidence: Mapping[str, Any]) -> TiamatState:
    fields: dict[str, Any] = {}
    for name in ("damage", "recovery", "residual_load", "excitation"):
        if name in evidence:
            fields[name] = float(evidence[name])
    for name in ("refractory", "promotion_count"):
        if name in evidence:
            fields[name] = int(evidence[name])
    if "timers" in evidence:
        fields["timers"] = dict(evidence["timers"])
    return replace(state, **fields) if fields else state


def transition(state: TiamatState, evidence: Mapping[str, Any], guard_results: tuple[GuardResult, ...] | None = None) -> TiamatState:
    """Pure deterministic TIAMAT transition shared by live execution and replay."""
    observed = _apply_measurements(state, evidence)
    guards = guard_results or evaluate_guards(observed, evidence)
    triggered = {g.name for g in guards if g.triggered}

    if "DURATION_DAMAGE_HAZARD_GUARD" in triggered or "LATENT_HAZARD_PRECURSOR_GUARD" in triggered:
        return replace(observed, mode=TiamatMode.HAZARD, promotion_count=observed.promotion_count + 1)
    if "RELAXATION_WITH_RESIDUAL_DAMAGE" in triggered:
        return replace(observed, mode=TiamatMode.HAZARD)
    if "COUPLED_TRANSFER_HAZARD_PROMOTION" in triggered:
        return replace(observed, mode=TiamatMode.HAZARD, promotion_count=observed.promotion_count + 1)
    if "EXCITATION_DURATION_EXPIRED" in triggered:
        return replace(observed, mode=TiamatMode.RELAXING)
    if observed.excitation > 0.0:
        return replace(observed, mode=TiamatMode.EXCITED)
    return replace(observed, mode=TiamatMode.IDLE)
