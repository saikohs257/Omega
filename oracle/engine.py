from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from court.engine import Verdict
from oracle.fusion import EvidenceClaim, FusionObject, fuse_claims


@dataclass(frozen=True, slots=True)
class Amendment:
    approved: bool
    reason: str
    changes: dict[str, Any]
    evidence: dict[str, Any]


@dataclass(slots=True)
class Oracle:
    amendments: list[Amendment] = field(default_factory=list)

    def fuse(
        self,
        claims: Sequence[EvidenceClaim],
        *,
        expected_channels: Sequence[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> FusionObject:
        """Fuse distributed evidence without granting transition authority."""
        return fuse_claims(
            claims,
            expected_channels=expected_channels,
            metadata=metadata,
        )

    def propose(self, verdict: Verdict, changes: Mapping[str, Any]) -> Amendment:
        amendment = Amendment(
            approved=verdict.approved,
            reason=verdict.reason,
            changes=dict(changes),
            evidence=dict(verdict.record),
        )
        if amendment.approved:
            self.amendments.append(amendment)
        return amendment

    def latest(self) -> Amendment | None:
        return self.amendments[-1] if self.amendments else None
