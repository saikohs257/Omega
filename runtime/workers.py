from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from runtime.events import Event
from runtime.operators import Operator
from runtime.trajectory import Trajectory


@dataclass(frozen=True, slots=True)
class WorkerTrace:
    worker_id: str
    operator: str
    before: dict[str, Any]
    after: dict[str, Any]
    event: Event


@dataclass(slots=True)
class Worker:
    """Single-operator worker. No direct worker-to-worker communication."""

    worker_id: str
    operator: Operator
    trajectory: Trajectory = field(default_factory=Trajectory)

    def run(self, state: Mapping[str, Any]) -> tuple[dict[str, Any], WorkerTrace]:
        before = dict(state)
        after = self.operator.apply(before)
        event = Event.create(
            "worker_run",
            payload={"worker_id": self.worker_id, "operator": self.operator.name},
            metadata={"before_keys": tuple(sorted(before.keys())), "after_keys": tuple(sorted(after.keys()))},
        )
        self.trajectory = self.trajectory.append(event)
        trace = WorkerTrace(
            worker_id=self.worker_id,
            operator=self.operator.name,
            before=before,
            after=dict(after),
            event=event,
        )
        return dict(after), trace
