from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from tiamat.engine import Decision


@dataclass(frozen=True, slots=True)
class Verdict:
    approved: bool
    reason: str
    decision: Decision
    record: dict[str, Any]


@dataclass(slots=True)
class Court:
    records: list[dict[str, Any]] = field(default_factory=list)

    def review(self, decision: Decision) -> Verdict:
        record = {
            "approved": decision.approved,
            "reason": decision.reason,
            "state_keys": tuple(sorted(decision.state.keys())),
        }
        self.records.append(record)
        return Verdict(approved=decision.approved, reason=decision.reason, decision=decision, record=record)
