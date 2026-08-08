from __future__ import annotations
from dataclasses import replace
from typing import Any, Mapping
from .guards import GuardResult, evaluate_guards
from .modes import TiamatMode
from .state import TiamatState

LEGAL = {
    TiamatMode.QUIESCENT: {TiamatMode.PRECURSOR},
    TiamatMode.PRECURSOR: {TiamatMode.EXCITATION, TiamatMode.QUIESCENT},
    TiamatMode.EXCITATION: {TiamatMode.COUPLED_TRANSFER, TiamatMode.HAZARD, TiamatMode.RELAXATION},
    TiamatMode.COUPLED_TRANSFER: {TiamatMode.HAZARD, TiamatMode.RELAXATION},
    TiamatMode.HAZARD: {TiamatMode.RELAXATION},
    TiamatMode.RELAXATION: {TiamatMode.QUIESCENT, TiamatMode.REFRACTORY, TiamatMode.HAZARD},
    TiamatMode.REFRACTORY: {TiamatMode.QUIESCENT},
}

def _finite(value: Any, name: str) -> float:
    value = float(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be finite")
    return value

def transition(state: TiamatState, evidence: Mapping[str, Any], guard_results: tuple[GuardResult, ...] | None = None) -> TiamatState:
    B = _finite(evidence.get("B", state.B), "B")
    V = _finite(evidence.get("V", state.V), "V")
    D = _finite(evidence.get("D", state.D), "D")
    candidate = replace(
        state,
        B=B,
        V=V,
        D=D,
        tau_D=_finite(evidence.get("tau_D", state.tau_D), "tau_D"),
        tau_mode=_finite(evidence.get("tau_mode", state.tau_mode + 1.0), "tau_mode"),
    )
    guards = guard_results or evaluate_guards(candidate, evidence)
    triggered = {g.name for g in guards if g.triggered}

    target = candidate.mode
    if candidate.mode is TiamatMode.RELAXATION and "RELAXATION_WITH_RESIDUAL_DAMAGE" in triggered:
        target = TiamatMode.HAZARD
    elif "DURATION_DAMAGE_HAZARD_GUARD" in triggered or "LATENT_HAZARD_PRECURSOR_GUARD" in triggered or "COUPLED_TRANSFER_HAZARD_PROMOTION" in triggered:
        target = TiamatMode.HAZARD
    elif "EXCITATION_DURATION_EXPIRED" in triggered and candidate.mode is TiamatMode.EXCITATION:
        target = TiamatMode.RELAXATION
    elif candidate.mode is TiamatMode.QUIESCENT and candidate.V > 0:
        target = TiamatMode.PRECURSOR
    elif candidate.mode is TiamatMode.PRECURSOR and candidate.V > 0 and candidate.B > 0:
        target = TiamatMode.EXCITATION
    elif candidate.mode is TiamatMode.EXCITATION and evidence.get("coupled_transfer"):
        target = TiamatMode.COUPLED_TRANSFER
    elif candidate.mode is TiamatMode.EXCITATION and candidate.V < 0:
        target = TiamatMode.RELAXATION
    elif candidate.mode is TiamatMode.COUPLED_TRANSFER and candidate.V < 0:
        target = TiamatMode.RELAXATION
    elif candidate.mode is TiamatMode.HAZARD and candidate.V < 0:
        target = TiamatMode.RELAXATION
    elif candidate.mode is TiamatMode.RELAXATION and candidate.D <= float(evidence.get("refractory_damage_threshold", 0.0)) and candidate.V >= 0:
        target = TiamatMode.QUIESCENT
    elif candidate.mode is TiamatMode.RELAXATION and evidence.get("enter_refractory"):
        target = TiamatMode.REFRACTORY
    elif candidate.mode is TiamatMode.REFRACTORY and evidence.get("refractory_release"):
        target = TiamatMode.QUIESCENT

    if target is not candidate.mode and target not in LEGAL.get(candidate.mode, set()):
        raise ValueError(f"illegal TIAMAT transition {candidate.mode.value}->{target.value}")
    if target is not candidate.mode:
        candidate = replace(candidate, mode=target, tau_mode=0.0)
    return candidate
