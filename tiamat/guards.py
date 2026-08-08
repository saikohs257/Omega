from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from .modes import TiamatMode
from .state import TiamatState

@dataclass(frozen=True, slots=True)
class GuardResult:
    name: str
    triggered: bool
    priority: int

class Guard:
    name = "UNNAMED"
    priority = 0
    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        raise NotImplementedError

class DamageHazardGuard(Guard):
    name = "DURATION_DAMAGE_HAZARD_GUARD"
    priority = 3
    def evaluate(self, state, evidence):
        threshold = evidence.get("damage_threshold")
        return threshold is not None and state.D >= float(threshold)

class ResidualDamageGuard(Guard):
    name = "RELAXATION_WITH_RESIDUAL_DAMAGE"
    priority = 3
    def evaluate(self, state, evidence):
        threshold = evidence.get("residual_threshold")
        return state.mode is TiamatMode.RELAXATION and threshold is not None and state.residual_load > float(threshold)

class ExcitationDurationGuard(Guard):
    name = "EXCITATION_DURATION_EXPIRED"
    priority = 2
    def evaluate(self, state, evidence):
        limit = evidence.get("excitation_duration")
        return limit is not None and float(limit) >= 0 and state.tau_mode >= float(limit)

class PrecursorHazardGuard(Guard):
    name = "LATENT_HAZARD_PRECURSOR_GUARD"
    priority = 2
    def evaluate(self, state, evidence):
        threshold = evidence.get("precursor_threshold")
        return threshold is not None and state.D + max(0.0, state.V) >= float(threshold)

class CoupledPromotionGuard(Guard):
    name = "COUPLED_TRANSFER_HAZARD_PROMOTION"
    priority = 1
    def evaluate(self, state, evidence):
        threshold = evidence.get("promotion_threshold")
        count = evidence.get("promotion_count")
        return threshold is not None and count is not None and int(count) >= int(threshold)

DEFAULT_GUARDS = (DamageHazardGuard(), ResidualDamageGuard(), ExcitationDurationGuard(), PrecursorHazardGuard(), CoupledPromotionGuard())

def evaluate_guards(state: TiamatState, evidence: Mapping[str, Any], guards=DEFAULT_GUARDS):
    return tuple(sorted((GuardResult(g.name, bool(g.evaluate(state, evidence)), g.priority) for g in guards), key=lambda r: -r.priority))
