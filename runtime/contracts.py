from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class OutputKind(str, Enum):
    DIAGNOSTIC_SCORE = "diagnostic_score"
    RISK_SCORE = "risk_score"
    HAZARD_SCORE = "hazard_score"
    PROBABILITY = "probability"
    DECISION = "decision"
    AUTHORITY = "authority"


class ContractViolation(ValueError):
    """Raised when an output is used with semantics it did not declare."""


@dataclass(frozen=True, slots=True)
class OutputContract:
    kind: OutputKind
    name: str
    version: str = "v1"
    metadata: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def create(cls, kind: OutputKind, name: str, metadata: Mapping[str, Any] | None = None) -> OutputContract:
        return cls(kind=kind, name=name, metadata=tuple(sorted((metadata or {}).items())))

    def require_probability(self) -> None:
        if self.kind is not OutputKind.PROBABILITY:
            raise ContractViolation(f"{self.name} declares {self.kind.value}, not probability")

    def is_probability(self) -> bool:
        return self.kind is OutputKind.PROBABILITY
