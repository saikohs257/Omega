from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from runtime.constitutional_record import ConstitutionalRecord
from runtime.state_vector import StateVector


class ReplayOperator(Protocol):
    def reconstruct(self, record: ConstitutionalRecord, state: StateVector) -> StateVector:
        ...


@dataclass(frozen=True, slots=True)
class RecordReplayOperator:
    """Deterministic baseline operator for constitutional records."""

    def reconstruct(self, record: ConstitutionalRecord, state: StateVector) -> StateVector:
        return state.with_updates(
            record_count=state.get("record_count", 0) + 1,
            last_record_type=record.record_type,
            last_record_id=record.record_id,
            last_payload=dict(record.payload),
        )


@dataclass(slots=True)
class ReplayRegistry:
    _operators: dict[str, ReplayOperator] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "*" not in self._operators:
            self._operators["*"] = RecordReplayOperator()

    def register(self, record_type: str, operator: ReplayOperator) -> None:
        if not isinstance(record_type, str) or not record_type:
            raise TypeError("record_type must be a non-empty string")
        reconstruct = getattr(operator, "reconstruct", None)
        if not callable(reconstruct):
            raise TypeError("operator must provide a callable reconstruct method")
        self._operators[record_type] = operator

    def resolve(self, record_type: str) -> ReplayOperator:
        if not isinstance(record_type, str) or not record_type:
            raise TypeError("record_type must be a non-empty string")
        try:
            return self._operators[record_type]
        except KeyError:
            return self._operators["*"]
