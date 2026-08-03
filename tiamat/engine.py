from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from runtime.events import Event
from runtime.replay import ReplayEngine
from runtime.trajectory import Trajectory


@dataclass(frozen=True, slots=True)
class Decision:
    approved: bool
    reason: str
    state: dict[str, Any]
    event: Event


@dataclass(slots=True)
class TiamatEngine:
    replay_engine: ReplayEngine = field(default_factory=ReplayEngine)

    def evaluate(self, state: Mapping[str, Any], request: Mapping[str, Any]) -> Decision:
        current = dict(state)
        if request.get("allow") is False:
            event = Event.create("tiamat_reject", dict(request), {"reason": "request disallowed"})
            return Decision(approved=False, reason="request disallowed", state=current, event=event)
        next_state = dict(current)
        next_state.update(request)
        event = Event.create("tiamat_approve", dict(request), {"reason": "request allowed"})
        return Decision(approved=True, reason="request allowed", state=next_state, event=event)

    def execute(self, state: Mapping[str, Any], request: Mapping[str, Any]) -> Decision:
        return self.evaluate(state, request)

    def replay(self, initial_state: Mapping[str, Any] | None, trajectory: Trajectory) -> dict[str, Any]:
        return self.replay_engine.replay(initial_state, trajectory).state
