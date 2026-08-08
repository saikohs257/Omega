from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class StateVector:
    """Immutable reconstructed runtime state."""

    values: Mapping[str, Any] = field(default_factory=dict)

    def with_updates(self, **updates: Any) -> StateVector:
        next_values = dict(self.values)
        next_values.update(updates)
        return StateVector(next_values)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.values)
