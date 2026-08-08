from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event
from runtime.replay import ReplayEngine
from runtime.state_vector import StateVector
from runtime.trajectory import Trajectory
from .replay import replay as replay_state
from .state import TiamatState
from .transition import transition
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
            return Decision(False, "request disallowed", current, event)
        next_state = dict(current); next_state.update(request)
        event = Event.create("tiamat_approve", dict(request), {"reason": "request allowed"})
        return Decision(True, "request allowed", next_state, event)
    def execute(self, state: Mapping[str, Any], request: Mapping[str, Any]) -> Decision:
        return self.evaluate(state, request)
    def transition_state(self, state: TiamatState, evidence: Mapping[str, Any]) -> TiamatState:
        return transition(state, evidence)
    def replay_state(self, initial_state: TiamatState, evidence: Sequence[Mapping[str, Any]]) -> TiamatState:
        return replay_state(initial_state, evidence)
    def replay(self, initial_state: Mapping[str, Any] | None, trajectory: Trajectory) -> dict[str, Any]:
        initial = StateVector(dict(initial_state or {}))
        records = tuple(ConstitutionalRecord(record_type=event.kind, payload=event.payload_dict(), timestamp=str(index)) for index, event in enumerate(trajectory))
        return self.replay_engine.replay(records, initial_state=initial).state_vector.as_dict()
