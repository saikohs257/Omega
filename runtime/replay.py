from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from runtime.events import Event
from runtime.trajectory import Trajectory


State = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReplayResult:
    state: State
    trajectory: Trajectory


class ReplayEngine:
    """Deterministic replay over an immutable trajectory."""

    def __init__(self) -> None:
        pass

    def replay(self, initial_state: Mapping[str, Any] | None, trajectory: Trajectory) -> ReplayResult:
        state: State = dict(initial_state or {})
        state["history"] = []
        state["event_count"] = 0

        for event in trajectory:
            state = self._apply_event(state, event)

        return ReplayResult(state=state, trajectory=trajectory)

    def _apply_event(self, state: State, event: Event) -> State:
        next_state: State = dict(state)
        history = list(next_state.get("history", []))
        history.append(
            {
                "kind": event.kind,
                "payload": event.payload_dict(),
                "metadata": event.metadata_dict(),
            }
        )
        next_state["history"] = history
        next_state["event_count"] = int(next_state.get("event_count", 0)) + 1
        next_state["last_event_kind"] = event.kind
        next_state["last_event_payload"] = event.payload_dict()
        next_state["last_event_metadata"] = event.metadata_dict()
        return next_state
