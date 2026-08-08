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


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _integer_count(value: Any) -> int | None:
    result = _finite_float(value)
    if result is None or not result.is_integer():
        return None
    return int(result)


class DamageHazardGuard(Guard):
    name = "DURATION_DAMAGE_HAZARD_GUARD"
    priority = 3

    def evaluate(self, state, evidence):
        threshold = _finite_float(evidence.get("damage_threshold"))
        return threshold is not None and state.D >= threshold


class ResidualDamageGuard(Guard):
    name = "RELAXATION_WITH_RESIDUAL_DAMAGE"
    priority = 3

    def evaluate(self, state, evidence):
        threshold = _finite_float(evidence.get("residual_threshold"))
        return (
            state.mode is TiamatMode.RELAXATION
            and threshold is not None
            and state.residual_load > threshold
        )


class ExcitationDurationGuard(Guard):
    name = "EXCITATION_DURATION_EXPIRED"
    priority = 2

    def evaluate(self, state, evidence):
        limit = _finite_float(evidence.get("excitation_duration"))
        return limit is not None and limit >= 0 and state.tau_mode >= limit


class PrecursorHazardGuard(Guard):
    name = "LATENT_HAZARD_PRECURSOR_GUARD"
    priority = 2

    def evaluate(self, state, evidence):
        threshold = _finite_float(evidence.get("precursor_threshold"))
        return threshold is not None and state.D + max(0.0, state.V) >= threshold


class CoupledPromotionGuard(Guard):
    name = "COUPLED_TRANSFER_HAZARD_PROMOTION"
    priority = 1

    def evaluate(self, state, evidence):
        threshold = _integer_count(evidence.get("promotion_threshold"))
        count = _integer_count(evidence.get("promotion_count"))
        return threshold is not None and count is not None and count >= threshold


DEFAULT_GUARDS = (
    DamageHazardGuard(),
    ResidualDamageGuard(),
    ExcitationDurationGuard(),
    PrecursorHazardGuard(),
    CoupledPromotionGuard(),
)


def evaluate_guards(state: TiamatState, evidence: Mapping[str, Any], guards=DEFAULT_GUARDS):
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping")
    return tuple(
        sorted(
            (GuardResult(g.name, bool(g.evaluate(state, evidence)), g.priority) for g in guards),
            key=lambda r: -r.priority,
        )
    )
