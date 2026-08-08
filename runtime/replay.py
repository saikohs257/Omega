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
        if initial_state is not None and not isinstance(initial_state, StateVector):
            raise TypeError("initial_state must be a StateVector or None")
        normalized_records = tuple(records)
        if any(not isinstance(record, ConstitutionalRecord) for record in normalized_records):
            raise TypeError("records must contain only ConstitutionalRecord instances")
        state = initial_state if initial_state is not None else StateVector()
        for record in normalized_records:
            operator = self.registry.resolve(record.record_type)
            state = operator.reconstruct(record, state)
        return ReplayResult(records=normalized_records, state_vector=state)
