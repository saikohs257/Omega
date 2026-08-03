from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


State = Mapping[str, Any]


class Operator(Protocol):
    name: str

    def apply(self, state: State) -> dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class IdentityOperator:
    name: str = "identity"

    def apply(self, state: State) -> dict[str, Any]:
        return dict(state)


@dataclass(frozen=True, slots=True)
class AnnotateOperator:
    name: str
    key: str
    value: Any

    def apply(self, state: State) -> dict[str, Any]:
        next_state = dict(state)
        next_state[self.key] = self.value
        return next_state
