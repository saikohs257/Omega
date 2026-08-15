from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .state import HydraEvidence, HydraState, _clamp01


class HydraModule(Protocol):
    name: str

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        """Return this module's normalized state estimate in [0, 1]."""


@dataclass(frozen=True, slots=True)
class HazardModule:
    name: str = "hazard"

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        return _clamp01(evidence.hazard_score)


@dataclass(frozen=True, slots=True)
class BurdenModule:
    name: str = "burden"

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        return _clamp01(evidence.live_deficit)


@dataclass(frozen=True, slots=True)
class RecoveryModule:
    name: str = "recovery"

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        return evidence.recovery_capacity


@dataclass(frozen=True, slots=True)
class TrajectoryModule:
    name: str = "trajectory"

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        """Estimate directional transition pressure.

        Version 0 uses hazard acceleration when prior state exists.  This is a
        deliberately small baseline that can later be replaced by a richer
        adaptive trajectory estimator without changing the shared-state contract.
        """
        delta = evidence.hazard_raw - state.hazard
        return _clamp01(0.5 + 0.5 * max(-1.0, min(1.0, delta)))


@dataclass(frozen=True, slots=True)
class PersistenceModule:
    name: str = "persistence"

    def update(self, evidence: HydraEvidence, state: HydraState) -> float:
        age = max(0, int(evidence.episode_age_h))
        return _clamp01(age / 24.0)


@dataclass(frozen=True, slots=True)
class LaneCoordinator:
    """Three topology-scoped projections built from shared module state."""
    name: str = "lanes"

    def route(self, previous_live_deficit: float | None) -> str:
        if previous_live_deficit is None:
            return "unknown"
        if previous_live_deficit <= 0.70:
            return "0_to_4"
        if previous_live_deficit <= 0.85:
            return "2_to_4"
        return "3_to_4"

    def score(self, path: str, hazard: float, burden: float, recovery: float, trajectory: float) -> float:
        """Minimal first-generation lane projections.

        These are deliberately interpretable starting projections, not promoted
        reconstructions of historical TIAMAT coefficients.
        """
        if path == "0_to_4":
            return _clamp01(0.50 * burden + 0.30 * (1.0 - recovery) + 0.20 * trajectory)
        if path == "2_to_4":
            return _clamp01(0.50 * hazard + 0.35 * burden + 0.15 * (1.0 - recovery))
        if path == "3_to_4":
            return _clamp01(0.55 * hazard + 0.30 * burden + 0.15 * trajectory)
        return _clamp01(0.33 * hazard + 0.33 * burden + 0.34 * (1.0 - recovery))
