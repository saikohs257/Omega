from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Tuple


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
    hysteresis: Tuple[str, ...] = ()
    timers: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("damage", "recovery", "residual_load", "excitation"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.refractory < 0 or self.promotion_count < 0:
            raise ValueError("timers and counters cannot be negative")
        object.__setattr__(self, "timers", dict(self.timers))

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
