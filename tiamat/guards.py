from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .state import TiamatState


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

    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        return state.damage >= float(evidence.get("damage_threshold", 1.0))


class RelaxationResidualDamageGuard(Guard):
    name = "RELAXATION_WITH_RESIDUAL_DAMAGE"

    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        return state.mode.value == "RELAXING" and state.residual_load > float(evidence.get("residual_threshold", 0.0))


class ExcitationDurationExpiredGuard(Guard):
    name = "EXCITATION_DURATION_EXPIRED"

    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        limit = int(evidence.get("excitation_duration", 0))
        age = int(state.excitation_age_h)
        return limit > 0 and age >= limit


class LatentHazardPrecursorGuard(Guard):
    name = "LATENT_HAZARD_PRECURSOR_GUARD"

    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        threshold = float(evidence.get("precursor_threshold", 1.0))
        return state.damage + state.residual_load >= threshold


class CoupledTransferHazardPromotionGuard(Guard):
    name = "COUPLED_TRANSFER_HAZARD_PROMOTION"

    def evaluate(self, state: TiamatState, evidence: Mapping[str, Any]) -> bool:
        threshold = int(evidence.get("promotion_threshold", 1))
        return state.promotion_count >= threshold


DEFAULT_GUARDS: tuple[Guard, ...] = (
    DurationDamageHazardGuard(),
    RelaxationResidualDamageGuard(),
    ExcitationDurationExpiredGuard(),
    LatentHazardPrecursorGuard(),
    CoupledTransferHazardPromotionGuard(),
)


def evaluate_guards(
    state: TiamatState,
    evidence: Mapping[str, Any],
    guards: tuple[Guard, ...] = DEFAULT_GUARDS,
) -> tuple[GuardResult, ...]:
    return tuple(GuardResult(g.name, bool(g.evaluate(state, evidence))) for g in guards)
