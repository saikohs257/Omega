from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping, Sequence

from .identification_registry import MODEL_REGISTRY, ModelSpec
from .modes import TiamatMode
from .state import TiamatState

CANONICAL_CONTROL_AXES: tuple[str, ...] = ("B", "V", "D", "tau_D", "tau_mode", "Phi")
NUMERIC_FIELDS: tuple[str, ...] = ("B", "V", "D", "tau_D", "tau_mode", "Phi")


def _finite(value: Any, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _bounded_unit(value: Any, name: str) -> float:
    value = _finite(value, name)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def axes_for_model(model_id: str) -> tuple[str, ...]:
    spec = MODEL_REGISTRY[model_id]
    if isinstance(spec.state, tuple):
        return spec.state
    return ()


@dataclass(frozen=True, slots=True)
class TelemetryRow:
    """One row of canonical identification telemetry.

    The row is deliberately neutral: it can be projected into any candidate
    model without asserting that the candidate is canonical.
    """

    B: float = 0.0
    V: float = 0.0
    D: float = 0.0
    tau_D: float = 0.0
    tau_mode: float = 0.0
    Phi: float = 0.0
    mode: TiamatMode = TiamatMode.QUIESCENT
    model_id: str = "M3"
    timestamp: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in NUMERIC_FIELDS:
            value = _finite(getattr(self, name), name)
            if name in {"B", "D"} and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
            if name in {"tau_D", "tau_mode"} and value < 0.0:
                raise ValueError(f"{name} cannot be negative")
            object.__setattr__(self, name, value)
        if not isinstance(self.mode, TiamatMode):
            object.__setattr__(self, "mode", TiamatMode(str(self.mode)))
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be non-empty")
        if self.timestamp is not None and not isinstance(self.timestamp, str):
            object.__setattr__(self, "timestamp", str(self.timestamp))
        object.__setattr__(self, "extras", dict(self.extras))

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any], *, model_id: str = "M3") -> TelemetryRow:
        extras = {
            key: value
            for key, value in row.items()
            if key not in {"B", "V", "D", "tau_D", "tau_mode", "Phi", "mode", "model_id", "timestamp"}
        }
        return cls(
            B=row.get("B", 0.0),
            V=row.get("V", 0.0),
            D=row.get("D", 0.0),
            tau_D=row.get("tau_D", 0.0),
            tau_mode=row.get("tau_mode", 0.0),
            Phi=row.get("Phi", 0.0),
            mode=row.get("mode", TiamatMode.QUIESCENT),
            model_id=str(row.get("model_id", model_id)),
            timestamp=row.get("timestamp"),
            extras=extras,
        )

    def to_state(self) -> TiamatState:
        return TiamatState(
            B=self.B,
            V=self.V,
            D=self.D,
            tau_D=self.tau_D,
            tau_mode=self.tau_mode,
            mode=self.mode,
            model_id=self.model_id,
        )

    def to_mapping(self) -> dict[str, Any]:
        payload = {
            "B": self.B,
            "V": self.V,
            "D": self.D,
            "tau_D": self.tau_D,
            "tau_mode": self.tau_mode,
            "Phi": self.Phi,
            "mode": self.mode.value,
            "model_id": self.model_id,
        }
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        payload.update(self.extras)
        return payload

    def active_axes(self, model_id: str | None = None, *, control_axes: Sequence[str] = CANONICAL_CONTROL_AXES) -> tuple[str, ...]:
        target = self.model_id if model_id is None else model_id
        if target == "M7":
            return tuple(control_axes)
        return axes_for_model(target)

    def project(self, model_id: str | None = None, *, control_axes: Sequence[str] = CANONICAL_CONTROL_AXES) -> dict[str, Any]:
        axes = self.active_axes(model_id, control_axes=control_axes)
        values = {axis: getattr(self, axis) for axis in axes if axis in NUMERIC_FIELDS}
        if "mode" in axes:
            values["mode"] = self.mode.value
        if "timestamp" in axes and self.timestamp is not None:
            values["timestamp"] = self.timestamp
        return values

    def supports(self, model_id: str | None = None, *, control_axes: Sequence[str] = CANONICAL_CONTROL_AXES) -> bool:
        for axis in self.active_axes(model_id, control_axes=control_axes):
            value = getattr(self, axis, None)
            if axis in {"B", "D"}:
                if value is None or not 0.0 <= float(value) <= 1.0:
                    return False
            elif axis in {"tau_D", "tau_mode"}:
                if value is None or float(value) < 0.0 or not math.isfinite(float(value)):
                    return False
            elif axis in {"V", "Phi"}:
                if value is None or not math.isfinite(float(value)):
                    return False
        return True


@dataclass(frozen=True, slots=True)
class TelemetryAdapter:
    """Neutral projection layer for candidate-state experiments."""

    control_axes: tuple[str, ...] = CANONICAL_CONTROL_AXES

    def normalize(self, row: Mapping[str, Any] | TelemetryRow, *, model_id: str = "M3") -> TelemetryRow:
        if isinstance(row, TelemetryRow):
            return row
        return TelemetryRow.from_mapping(row, model_id=model_id)

    def frame(
        self,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        model_id: str,
    ) -> tuple[dict[str, Any], ...]:
        normalized = tuple(self.normalize(row, model_id=model_id) for row in rows)
        return tuple(row.project(model_id, control_axes=self.control_axes) for row in normalized)

    def states(
        self,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        model_id: str = "M3",
    ) -> tuple[TiamatState, ...]:
        return tuple(self.normalize(row, model_id=model_id).to_state() for row in rows)

    def supported_rows(
        self,
        rows: Sequence[Mapping[str, Any] | TelemetryRow],
        model_id: str,
    ) -> tuple[TelemetryRow, ...]:
        normalized = tuple(self.normalize(row, model_id=model_id) for row in rows)
        return tuple(row for row in normalized if row.supports(model_id, control_axes=self.control_axes))
