"""Canonical DIC evidence contract.

DIC is a collective of evidence-producing mechanisms, not a controller.
Adapters should translate historical sidecar outputs into EvidenceClaim
without inventing unavailable historical semantics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SidecarEvidence:
    source: str
    target_phase: str
    value: Any
    confidence: float
    freshness: float = 1.0
    dimensions: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    state_observation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not 0.0 <= self.freshness <= 1.0:
            raise ValueError("freshness must be in [0, 1]")

    def to_claim(self):
        from oracle.fusion import EvidenceClaim
        return EvidenceClaim(
            source=self.source,
            target_phase=self.target_phase,
            value=self.value,
            confidence=self.confidence,
            freshness=self.freshness,
            dimensions=self.dimensions,
            provenance=self.provenance,
        )


class DIC:
    """Collect sidecar evidence without interpreting or authorizing it."""

    def __init__(self) -> None:
        self._claims: list[SidecarEvidence] = []

    def emit(self, evidence: SidecarEvidence) -> None:
        self._claims.append(evidence)

    def claims(self) -> tuple[SidecarEvidence, ...]:
        return tuple(self._claims)

    def clear(self) -> None:
        self._claims.clear()

    def to_oracle_claims(self):
        return tuple(item.to_claim() for item in self._claims)
