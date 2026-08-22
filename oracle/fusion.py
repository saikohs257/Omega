"""Evidence-preserving Oracle fusion primitives.

This module is deliberately domain-neutral.  It does not authorize TIAMAT
transitions and does not collapse distributed evidence into a scalar score.
It converts independently produced claims into a replayable FusionObject.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    source: str
    target_phase: str
    value: Any
    confidence: float
    freshness: float = 1.0
    dimensions: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not 0.0 <= self.freshness <= 1.0:
            raise ValueError("freshness must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class FusionObject:
    claims: tuple[EvidenceClaim, ...]
    agreement: float
    disagreement: float
    missing_channels: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.source for c in self.claims))

    @property
    def phases(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.target_phase for c in self.claims))

    @property
    def confidence(self) -> float:
        if not self.claims:
            return 0.0
        return sum(c.confidence * c.freshness for c in self.claims) / len(self.claims)


def fuse_claims(
    claims: Sequence[EvidenceClaim],
    *,
    expected_channels: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> FusionObject:
    """Preserve distributed evidence and quantify agreement/disagreement.

    Claims are never averaged into a domain decision.  Agreement is based on
    matching ``(target_phase, value)`` pairs; differing values in the same
    phase are retained as contradictions.  This is intentionally conservative:
    downstream ERK/TIAMAT owns interpretation and authority.
    """
    ordered = tuple(claims)
    by_phase: dict[str, list[EvidenceClaim]] = {}
    for claim in ordered:
        by_phase.setdefault(claim.target_phase, []).append(claim)

    contradictions: list[str] = []
    agreements = 0
    comparisons = 0
    for phase, phase_claims in by_phase.items():
        values = {repr(c.value) for c in phase_claims}
        if len(values) > 1:
            contradictions.append(phase)
        n = len(phase_claims)
        comparisons += n * (n - 1) // 2
        agreements += n * (n - 1) // 2 if len(values) == 1 else 0

    agreement = agreements / comparisons if comparisons else (1.0 if ordered else 0.0)
    disagreement = 1.0 - agreement
    present = {c.source for c in ordered}
    missing = tuple(channel for channel in expected_channels if channel not in present)

    return FusionObject(
        claims=ordered,
        agreement=agreement,
        disagreement=disagreement,
        missing_channels=missing,
        contradictions=tuple(contradictions),
        metadata=dict(metadata or {}),
    )
