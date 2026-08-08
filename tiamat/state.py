from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping


class TiamatMode(str, Enum):
    IDLE = "IDLE"
    EXCITED = "EXCITED"
    RELAXING = "RELAXING"
    HAZARD = "HAZARD"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class TiamatState:
    mode: TiamatMode = TiamatMode.IDLE
    damage: float = 0.0
    recovery: float = 0.0
    residual_load: float = 0.0
    excitation: float = 0.0
    refractory: int = 0
    promotion_count: int = 0
    hysteresis: tuple[str, ...] = ()
    timers: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("damage", "recovery", "residual_load", "excitation"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.refractory < 0 or self.promotion_count < 0:
            raise ValueError("timers and counters cannot be negative")
        frozen_timers = {str(key): int(value) for key, value in self.timers.items()}
        if any(value < 0 for value in frozen_timers.values()):
            raise ValueError("timer values cannot be negative")
        object.__setattr__(self, "hysteresis", tuple(self.hysteresis))
        object.__setattr__(self, "timers", MappingProxyType(frozen_timers))

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "TiamatState":
        mode = value.get("mode", TiamatMode.IDLE)
        if not isinstance(mode, TiamatMode):
            mode = TiamatMode(str(mode))
        return cls(
            mode=mode,
            damage=float(value.get("damage", 0.0)),
            recovery=float(value.get("recovery", 0.0)),
            residual_load=float(value.get("residual_load", 0.0)),
            excitation=float(value.get("excitation", 0.0)),
            refractory=int(value.get("refractory", 0)),
            promotion_count=int(value.get("promotion_count", 0)),
            hysteresis=tuple(value.get("hysteresis", ())),
            timers=dict(value.get("timers", {})),
        )

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "damage": self.damage,
            "recovery": self.recovery,
            "residual_load": self.residual_load,
            "excitation": self.excitation,
            "refractory": self.refractory,
            "promotion_count": self.promotion_count,
            "hysteresis": list(self.hysteresis),
            "timers": dict(sorted(self.timers.items())),
        }
