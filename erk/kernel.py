from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence
import hashlib
import json

from .core import Action, Authority, EpistemicState, EvidenceRecord, PolicyConfig, Supervisor, Transition, _canonical


class ConstitutionalViolation(RuntimeError):
    """Raised when a requested transition is not constitutionally admissible."""


@dataclass(frozen=True, slots=True)
class KernelConfig:
    policy: PolicyConfig = PolicyConfig()
    require_monotonic_evidence_count: bool = True


class ConstitutionalKernel:
    """Small executable boundary between policy selection and state mutation.

    The kernel does not reason. It validates an action against the current state,
    then delegates the actual state transition to the deterministic Transition
    primitive. Illegal actions cannot be applied through this boundary.
    """

    def __init__(self, config: KernelConfig | None = None) -> None:
        self.config = config or KernelConfig()
        self.supervisor = Supervisor(self.config.policy)

    def admissible(self, state: EpistemicState, action: Action) -> bool:
        return action in self.supervisor.safe_actions(state)

    def step(
        self,
        state: EpistemicState,
        action: Action,
        evidence: Sequence[EvidenceRecord] = (),
    ) -> EpistemicState:
        if not self.admissible(state, action):
            raise ConstitutionalViolation(f"inadmissible action: {action}")
        before = state.normalized()
        after = Transition.apply(before, action, evidence)
        if self.config.require_monotonic_evidence_count and after.evidence_count < before.evidence_count:
            raise ConstitutionalViolation("evidence count decreased")
        if action == Action.ENABLE_EXECUTION and after.authority >= Authority.EXECUTE:
            raise ConstitutionalViolation("execution failed to consume authority")
        return after

    def replay(
        self,
        initial: EpistemicState,
        events: Sequence[tuple[Action, Sequence[EvidenceRecord]]],
    ) -> tuple[EpistemicState, ...]:
        states = [initial.normalized()]
        current = states[0]
        for action, evidence in events:
            current = self.step(current, action, evidence)
            states.append(current)
        return tuple(states)

    @staticmethod
    def replay_hash(states: Sequence[EpistemicState]) -> str:
        payload = [
            {
                "state": _canonical({
                    "observability": dict(s.observability),
                    "hypotheses": dict(s.hypotheses),
                    "predictions": dict(s.predictions),
                    "relevance": dict(s.relevance),
                    "strain": s.strain,
                    "unsupported_depth": s.unsupported_depth,
                    "critical_load": dict(s.critical_load),
                    "cycles": s.cycles,
                    "authority": int(s.authority),
                    "calibration_error": s.calibration_error,
                    "active_branches": s.active_branches,
                    "evidence_count": s.evidence_count,
                    "policy_version": s.policy_version,
                })
            }
            for s in states
        ]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
