from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event
from runtime.replay import ReplayEngine
from runtime.state_vector import StateVector
from runtime.trajectory import Trajectory

from .dynamics import DynamicsSnapshot, hazard_score, residual_load
from .guards import evaluate_guards
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
    """Full deterministic TIAMAT runtime facade.

    ``transition`` remains the single state-update authority.  The engine adds
    diagnostic projection, guard telemetry, and replay without maintaining a
    second state machine.
    """

    replay_engine: ReplayEngine = field(default_factory=ReplayEngine)

    def step(self, state: TiamatState, evidence: Mapping[str, Any]) -> TiamatState:
        """Advance the canonical seven-mode state machine by one evidence row."""
        return transition(state, evidence)

    def diagnose(self, state: TiamatState, evidence: Mapping[str, Any]) -> dict[str, Any]:
        """Return the complete observable/guard projection for one step."""
        next_state = transition(state, evidence)
        guards = evaluate_guards(next_state, evidence)
        raw_hazard = float(evidence.get("hazard_raw", next_state.D + max(0.0, next_state.V)))
        return {
            "state": next_state.to_dict(),
            "guards": tuple(
                {"name": result.name, "triggered": result.triggered, "priority": result.priority}
                for result in guards
            ),
            "observables": {
                "recovery": next_state.recovery,
                "pressure": next_state.pressure,
                "momentum": next_state.momentum,
                "residual_load": residual_load(next_state.D, next_state.recovery),
                "hazard_raw": raw_hazard,
                "hazard_score": hazard_score(raw_hazard),
            },
            "context": {
                key: evidence[key]
                for key in (
                    "initial_velocity",
                    "initial_momentum",
                    "initial_trajectory",
                    "trajectory",
                    "path",
                    "arc",
                    "route",
                    "track",
                    "orbit",
                    "resistance",
                    "charge",
                    "flow",
                    "coupling",
                    "arrival_context",
                    "hysteresis_memory",
                )
                if key in evidence
            },
        }

    def evaluate(self, state: Mapping[str, Any], request: Mapping[str, Any]) -> Decision:
        """Evaluate a request through the TIAMAT state machine when state evidence is supplied.

        The legacy permission-only path remains available for non-TIAMAT callers,
        but canonical TIAMAT callers should provide B/V/D or a mode-bearing state.
        """
        current = dict(state)
        tiamat_keys = {"B", "V", "D", "mode", "damage_threshold", "residual_threshold", "precursor_threshold"}
        if tiamat_keys.intersection(current) or tiamat_keys.intersection(request):
            initial = TiamatState.from_mapping(current)
            next_state = transition(initial, request)
            payload = next_state.to_dict()
            event = Event.create("tiamat_transition", dict(request), payload)
            return Decision(True, f"TIAMAT transition {initial.mode.value}->{next_state.mode.value}", payload, event)
        if request.get("allow") is False:
            event = Event.create("tiamat_reject", dict(request), {"reason": "request disallowed"})
            return Decision(False, "request disallowed", current, event)
        next_state = dict(current)
        next_state.update(request)
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
        records = tuple(
            ConstitutionalRecord(
                record_type=event.kind,
                payload=event.payload_dict(),
                timestamp=str(index),
            )
            for index, event in enumerate(trajectory)
        )
        return self.replay_engine.replay(records, initial_state=initial).state_vector.as_dict()
