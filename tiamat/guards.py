from __future__ import annotations
from dataclasses import dataclass
import math
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


def _finite_number(value: Any) -> float | None:
    """Accept real finite numeric evidence, explicitly excluding bool."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


class DamageHazardGuard(Guard):
    name = "DURATION_DAMAGE_HAZARD_GUARD"
    priority = 3
    def evaluate(self, state, evidence):
        threshold = _finite_number(evidence.get("damage_threshold"))
        return threshold is not None and state.D >= threshold

class ResidualDamageGuard(Guard):
    name = "RELAXATION_WITH_RESIDUAL_DAMAGE"
    priority = 3
    def evaluate(self, state, evidence):
        threshold = _finite_number(evidence.get("residual_threshold"))
        return state.mode is TiamatMode.RELAXATION and threshold is not None and state.residual_load > threshold

class ExcitationDurationGuard(Guard):
    name = "EXCITATION_DURATION_EXPIRED"
    priority = 2
    def evaluate(self, state, evidence):
        limit = _finite_number(evidence.get("excitation_duration"))
        return limit is not None and limit >= 0 and state.tau_mode >= limit

class PrecursorHazardGuard(Guard):
    name = "LATENT_HAZARD_PRECURSOR_GUARD"
    priority = 2
    def evaluate(self, state, evidence):
        threshold = _finite_number(evidence.get("precursor_threshold"))
        return threshold is not None and state.D + max(0.0, state.V) >= threshold

class CoupledPromotionGuard(Guard):
    name = "COUPLED_TRANSFER_HAZARD_PROMOTION"
    priority = 1
    def evaluate(self, state, evidence):
        threshold = _finite_number(evidence.get("promotion_threshold"))
        count = _finite_number(evidence.get("promotion_count"))
        if threshold is None or count is None:
            return False
        if not count.is_integer() or not threshold.is_integer():
            return False
        return int(count) >= int(threshold)

DEFAULT_GUARDS = (DamageHazardGuard(), ResidualDamageGuard(), ExcitationDurationGuard(), PrecursorHazardGuard(), CoupledPromotionGuard())

def evaluate_guards(state: TiamatState, evidence: Mapping[str, Any], guards=DEFAULT_GUARDS):
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping")
    return tuple(sorted((GuardResult(g.name, bool(g.evaluate(state, evidence)), g.priority) for g in guards), key=lambda r: -r.priority))
