from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from runtime.replay_protocol import ReplayOperator


@dataclass(slots=True)
class ReplayRegistry:
    """Constitutional registry from record types to replay operators."""

    _operators: dict[str, ReplayOperator] = field(default_factory=dict)

    def register(self, operator: ReplayOperator) -> None:
        for record_type in operator.consumes():
            if record_type in self._operators:
                raise ValueError(f"duplicate replay jurisdiction for {record_type!r}")
            self._operators[record_type] = operator

    def lookup(self, record_type: str) -> ReplayOperator | None:
        return self._operators.get(record_type)

    def record_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._operators))
