from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

from runtime.state_vector import StateVector


@dataclass(frozen=True, slots=True)
class Invariant:
    """Declarative invariant used by replay validation."""

    name: str
    description: str = ""


class ReplayOperator(Protocol):
    """Subsystem-level replay contract.

    Replay never imports subsystem implementations directly. Subsystems
    register operators that consume records and reconstruct state slices.
    """

    jurisdiction: str

    def consumes(self) -> tuple[str, ...]:
        ...

    def reconstruct(self, record: Any, state: StateVector) -> StateVector:
        ...

    def invariants(self) -> tuple[Invariant, ...]:
        ...
