from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class StateVector:
    """Immutable reconstructed runtime state."""

    values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping):
            raise TypeError("values must be a mapping")
        if any(not isinstance(key, str) for key in self.values):
            raise TypeError("values keys must be strings")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def with_updates(self, **updates: Any) -> StateVector:
        next_values = dict(self.values)
        next_values.update(updates)
        return StateVector(next_values)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.values)
