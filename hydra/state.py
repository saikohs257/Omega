from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional


def _clamp01(value: float) -> float:
    value = float(value)
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass(frozen=True, slots=True)
class HydraEvidence:
    """One timestamp of causal evidence supplied to HYDRA.

    Inputs intentionally mirror the recovered TIAMAT substrate where available,
    while allowing newer modules to consume additional raw/derived measurements
    without changing the state contract.
    """

    hazard_raw: float
    hazard_score: float
    live_deficit: float
    simple_shock: float
    recovery_weakness: float
    episode_age_h: int = 0
    prev_live_deficit: Optional[float] = None
    tempo24: float = 0.0
    tempo48: float = 0.0
    regime: str = "unknown"

    @property
    def recovery_capacity(self) -> float:
        return 1.0 - _clamp01(self.recovery_weakness)

    @property
    def unresolved_load(self) -> float:
        return max(0.0, _clamp01(self.live_deficit) - self.recovery_capacity)

    @property
    def hazard_delta(self) -> Optional[float]:
        if self.prev_live_deficit is None:
            return None
        return float(self.hazard_raw)  # explicit placeholder: delta is derived by engine history


@dataclass(frozen=True, slots=True)
class HydraState:
    """Shared state bus plus module outputs.

    Each compartment owns its own interpretation. The coordinator never discards
    module disagreement; ``tension`` is part of the public state because conflicting
    sensors often mark the transition states that HYDRA is designed to find.
    """

    hazard: float = 0.0
    burden: float = 0.0
    recovery: float = 1.0
    trajectory: float = 0.0
    persistence: int = 0
    entry_path: str = "unknown"
    lane_scores: Mapping[str, float] = field(default_factory=dict)
    lane_states: Mapping[str, str] = field(default_factory=dict)
    active: bool = False
    tension: float = 0.0
    confidence: float = 0.0

    def with_updates(self, **updates: object) -> "HydraState":
        values = {
            "hazard": self.hazard,
            "burden": self.burden,
            "recovery": self.recovery,
            "trajectory": self.trajectory,
            "persistence": self.persistence,
            "entry_path": self.entry_path,
            "lane_scores": dict(self.lane_scores),
            "lane_states": dict(self.lane_states),
            "active": self.active,
            "tension": self.tension,
            "confidence": self.confidence,
        }
        values.update(updates)
        return HydraState(**values)


@dataclass(frozen=True, slots=True)
class HydraDecision:
    """Coordinator output; preserves all module explanations."""

    state: HydraState
    action: str
    reason: str
    module_votes: Mapping[str, str]
    module_scores: Mapping[str, float]
    disagreements: Mapping[str, float]
