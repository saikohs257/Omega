from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from .state import TiamatMode, TiamatState

@dataclass(frozen=True, slots=True)
class GuardResult:
    name: str
    triggered: bool

class Guard:
    name = "UNNAMED"
    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        raise NotImplementedError

class DurationDamageHazardGuard(Guard):
    name = "DURATION_DAMAGE_HAZARD_GUARD"
    def evaluate(self, state, evidence): return state.damage >= float(evidence.get("damage_threshold", 1.0))

class RelaxationResidualDamageGuard(Guard):
    name = "RELAXATION_WITH_RESIDUAL_DAMAGE"
    def evaluate(self, state, evidence): return state.mode is TiamatMode.RELAXING and state.residual_load > float(evidence.get("residual_threshold", 0.0))

class ExcitationDurationExpiredGuard(Guard):
    name = "EXCITATION_DURATION_EXPIRED"
    def evaluate(self, state, evidence):
        limit = int(evidence.get("excitation_duration", 0))
        return limit > 0 and state.excitation_age_h >= limit

class LatentHazardPrecursorGuard(Guard):
    name = "LATENT_HAZARD_PRECURSOR_GUARD"
    def evaluate(self, state, evidence): return state.damage + state.residual_load >= float(evidence.get("precursor_threshold", 1.0))

class CoupledTransferHazardPromotionGuard(Guard):
    name = "COUPLED_TRANSFER_HAZARD_PROMOTION"
    def evaluate(self, state, evidence): return state.promotion_count >= int(evidence.get("promotion_threshold", 1))

DEFAULT_GUARDS = (DurationDamageHazardGuard(), RelaxationResidualDamageGuard(), ExcitationDurationExpiredGuard(), LatentHazardPrecursorGuard(), CoupledTransferHazardPromotionGuard())

def evaluate_guards(state: TiamatState, evidence: Mapping[str, Any], guards=DEFAULT_GUARDS):
    return tuple(GuardResult(g.name, bool(g.evaluate(state, evidence))) for g in guards)
