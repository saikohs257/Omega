from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

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

    def replay(
        self,
        records: Sequence[ConstitutionalRecord],
        initial_state: StateVector | None = None,
    ) -> ReplayResult:
        state = initial_state or StateVector()
        normalized_records = tuple(records)
        for record in normalized_records:
            operator = self.registry.resolve(record.record_type)
            state = operator.reconstruct(record, state)
        return ReplayResult(records=normalized_records, state_vector=state)
