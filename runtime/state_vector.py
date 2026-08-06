from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class StateVector:
    """Immutable reconstructed organism state.

    The state vector is the only authoritative runtime output of replay.
    It is intentionally generic: subsystem-specific slices live in the payload.
    """

    slices: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    version: str = "state-vector-v1"

    def get(self, key: str, default: Any = None) -> Any:
        for existing_key, value in self.slices:
            if existing_key == key:
                return value
        return default

    def with_slice(self, key: str, value: Any) -> "StateVector":
        updated = dict(self.slices)
        updated[key] = value
        return StateVector(slices=tuple(sorted(updated.items())), version=self.version)

    def merged(self, **updates: Any) -> "StateVector":
        updated = dict(self.slices)
        updated.update(updates)
        return StateVector(slices=tuple(sorted(updated.items())), version=self.version)
