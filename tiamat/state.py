from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Any

from .modes import TiamatMode


# Historical compact wire tokens are accepted on input, but canonical output
# is always the full TIAMAT mode name exposed by TiamatMode.value.
_LEGACY_MODE_VALUES = {
    "Q": TiamatMode.QUIESCENT,
    "P": TiamatMode.PRECURSOR,
    "E": TiamatMode.EXCITATION,
    "C": TiamatMode.COUPLED_TRANSFER,
    "H": TiamatMode.HAZARD,
    "R": TiamatMode.RELAXATION,
    "Rf": TiamatMode.REFRACTORY,
}


def _coerce_mode(value: Any) -> TiamatMode:
    """Accept canonical enum values, names, and legacy compact wire tokens."""
    if isinstance(value, TiamatMode):
        return value
    text = str(value)
    try:
        return TiamatMode(text)
    except ValueError:
        if text in _LEGACY_MODE_VALUES:
            return _LEGACY_MODE_VALUES[text]
        try:
            return TiamatMode[text]
        except KeyError:
            raise ValueError(f"{text!r} is not a valid TiamatMode") from None


@dataclass(frozen=True, slots=True)
class TiamatState:
    """M3 primary candidate state with optional temporal memory.

    B, V, D are the primitive identification coordinates. tau_D and tau_mode
    are conditional memory variables; they are not fixed choke timers.
    Recovery, residual load, and momentum are derived observables.
    """
    B: float = 0.0
    V: float = 0.0
    D: float = 0.0
    tau_D: float = 0.0
    tau_mode: float = 0.0
    mode: TiamatMode = TiamatMode.QUIESCENT
    model_id: str = "M3"

    def __post_init__(self) -> None:
        for name in ("B", "D", "tau_D", "tau_mode"):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if name in ("B", "D") and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
            if name in ("tau_D", "tau_mode") and value < 0.0:
                raise ValueError(f"{name} cannot be negative")
        if not math.isfinite(float(self.V)):
            raise ValueError("V must be finite")
        if not isinstance(self.mode, TiamatMode):
            object.__setattr__(self, "mode", _coerce_mode(self.mode))
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be non-empty")

    @property
    def recovery(self) -> float:
        return max(0.0, -self.V)

    @property
    def pressure(self) -> float:
        return max(0.0, self.V)

    @property
    def momentum(self) -> float:
        return self.V

    @property
    def residual_load(self) -> float:
        return max(0.0, self.D - self.recovery)

    def to_dict(self) -> dict[str, Any]:
        return {
            "B": self.B,
            "V": self.V,
            "D": self.D,
            "tau_D": self.tau_D,
            "tau_mode": self.tau_mode,
            "mode": self.mode.value,
            "model_id": self.model_id,
            "recovery": self.recovery,
            "pressure": self.pressure,
            "momentum": self.momentum,
            "residual_load": self.residual_load,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TiamatState":
        return cls(
            B=float(value.get("B", 0.0)),
            V=float(value.get("V", 0.0)),
            D=float(value.get("D", 0.0)),
            tau_D=float(value.get("tau_D", 0.0)),
            tau_mode=float(value.get("tau_mode", 0.0)),
            mode=_coerce_mode(value.get("mode", TiamatMode.QUIESCENT)),
            model_id=str(value.get("model_id", "M3")),
        )
