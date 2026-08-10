from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Mapping, Sequence


class OutputKind(str, Enum):
    DIAGNOSTIC_SCORE = "diagnostic_score"
    RISK_SCORE = "risk_score"
    HAZARD_SCORE = "hazard_score"
    PROBABILITY = "probability"
    DECISION = "decision"
    AUTHORITY = "authority"


class ContractViolation(ValueError):
    """Raised when an output is used with semantics it did not declare."""


class PreflightStatus(str, Enum):
    VALID = "VALID"
    INCOMPARABLE = "INCOMPARABLE"


@dataclass(frozen=True, slots=True)
class PreflightResult:
    """Non-fatal result of predictor contract preflight."""

    status: PreflightStatus
    reason: str = ""

    @property
    def comparable(self) -> bool:
        return self.status is PreflightStatus.VALID


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


@dataclass(frozen=True, slots=True)
class ProbabilityContract:
    """Contract for a predictor whose output is eligible for probability metrics."""

    version: str = "probability-v1"
    minimum: float = 0.0
    maximum: float = 1.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.minimum) or not math.isfinite(self.maximum):
            raise ValueError("probability bounds must be finite")
        if self.minimum < 0.0 or self.maximum > 1.0 or self.minimum >= self.maximum:
            raise ValueError("probability bounds must satisfy 0 <= minimum < maximum <= 1")
        if not self.version:
            raise ValueError("probability contract version must be non-empty")

    def validate(self, values: Sequence[float]) -> None:
        """Raise ContractViolation if any predictor output violates the probability contract."""
        for index, value in enumerate(values):
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise ContractViolation(f"probability output at index {index} is not numeric") from exc
            if not math.isfinite(numeric) or numeric < self.minimum or numeric > self.maximum:
                raise ContractViolation(
                    f"probability output at index {index}={value!r} is outside [{self.minimum}, {self.maximum}]"
                )

    def preflight(self, values: Sequence[float]) -> PreflightResult:
        """Partition a predictor before scoring without aborting the enclosing run."""
        try:
            self.validate(values)
        except ContractViolation as exc:
            return PreflightResult(PreflightStatus.INCOMPARABLE, str(exc))
        return PreflightResult(PreflightStatus.VALID)
