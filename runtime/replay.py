from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from runtime.events import Event
from runtime.trajectory import Trajectory


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Deterministic reconstruction result for the canonical runtime trajectory."""

    state: Mapping[str, Any]
    trajectory: Trajectory


class ReplayEngine:
    """Pure replay engine for the current runtime event model.

    The previous implementation referenced removed ``ConstitutionalRecord``,
    ``ReplayRegistry`` and ``StateVector`` modules and exposed an incompatible
    API. Replay is now deliberately small: the event trajectory is the source
    of truth and the reconstructed state is derived only from those events.
    """

    @staticmethod
    def replay(initial_state: Mapping[str, Any] | None, trajectory: Trajectory) -> ReplayResult:
        state = dict(initial_state or {})
        state["event_count"] = 0
        state.pop("last_event_kind", None)

        for event in trajectory:
            state["event_count"] += 1
            state["last_event_kind"] = event.kind

        return ReplayResult(state=state, trajectory=trajectory)
