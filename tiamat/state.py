from __future__

from dataclasses import dataclass
from enum import Enum
import math
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
    excitation: float = 0.0
    damage: float = 0.0
    recovery: float = 0.0
    residual_load: float = 0.0
    momentum: float = 0.0
    mode_age_h: int = 0
    excitation_age_h: int = 0
    relaxation_age_h: int = 0
    refractory_age_h: int = 0
    promotion_count: int = 0
    arrival_class: str = "UNKNOWN"
    hysteresis_memory: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("excitation", "damage", "recovery", "residual_load", "momentum"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        for name in ("mode_age_h", "excitation_age_h", "relaxation_age_h", "refractory_age_h", "promotion_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or int(value) != value or int(value) < 0:
                raise ValueError(f"{name} cannot be negative")
        if not isinstance(self.arrival_class, str) or not self.arrival_class:
            raise ValueError("arrival_class must be a non-empty string")
        object.__setattr__(self, "hysteresis_memory", tuple(self.hysteresis_memory))

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "TiamatState":
        mode = value.get("mode", TiamatMode.IDLE)
        if not isinstance(mode, TiamatMode):
            mode = TiamatMode(str(mode))
        return cls(mode=mode, excitation=float(value.get("excitation", 0.0)), damage=float(value.get("damage", 0.0)), recovery=float(value.get("recovery", 0.0)), residual_load=float(value.get("residual_load", 0.0)), momentum=float(value.get("momentum", 0.0)), mode_age_h=int(value.get("mode_age_h", 0)), excitation_age_h=int(value.get("excitation_age_h", 0)), relaxation_age_h=int(value.get("relaxation_age_h", 0)), refractory_age_h=int(value.get("refractory_age_h", 0)), promotion_count=int(value.get("promotion_count", 0)), arrival_class=str(value.get("arrival_class", "UNKNOWN")), hysteresis_memory=tuple(value.get("hysteresis_memory", ())))

    def to_dict(self) -> dict:
        return {"mode": self.mode.value, "excitation": self.excitation, "damage": self.damage, "recovery": self.recovery, "residual_load": self.residual_load, "momentum": self.momentum, "mode_age_h": self.mode_age_h, "excitation_age_h": self.excitation_age_h, "relaxation_age_h": self.relaxation_age_h, "refractory_age_h": self.refractory_age_h, "promotion_count": self.promotion_count, "arrival_class": self.arrival_class, "hysteresis_memory": list(self.hysteresis_memory)}
