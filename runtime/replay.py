from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from runtime.constitutional_record import ConstitutionalRecord
from runtime.replay_registry import ReplayRegistry
from runtime.state_vector import StateVector


@dataclass(frozen=True, slots=True)
class ReplayResult:
    records: tuple[ConstitutionalRecord, ...]
    state_vector: StateVector
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReplayEngine:
    registry: ReplayRegistry = field(default_factory=ReplayRegistry)

    def replay(self, records: tuple[ConstitutionalRecord, ...]) -> ReplayResult:
        state = StateVector()
        for record in records:
            operator = self.registry.resolve(record.record_type)
            state = operator.reconstruct(record, state)
        return ReplayResult(records=records, state_vector=state)
