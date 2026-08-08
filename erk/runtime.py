from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .core import Action, EpistemicState, EvidenceRecord
from .kernel import ConstitutionalKernel


@dataclass(frozen=True, slots=True)
class RuntimeStep:
    before: EpistemicState
    action: Action
    after: EpistemicState


@dataclass(slots=True)
class ConstitutionalRuntime:
    """Deterministic execution facade over the constitutional kernel."""

    kernel: ConstitutionalKernel = field(default_factory=ConstitutionalKernel)

    def choose(self, state: EpistemicState) -> Action:
        if not isinstance(state, EpistemicState):
            raise TypeError("state must be an EpistemicState")
        return self.kernel.supervisor.supervise(state)

    @staticmethod
    def _validate_action(action: Action | None) -> None:
        if action is not None and not isinstance(action, Action):
            raise TypeError("action must be an Action or None")

    @staticmethod
    def _normalize_evidence(evidence: Sequence[EvidenceRecord]) -> tuple[EvidenceRecord, ...]:
        normalized = tuple(evidence)
        if any(not isinstance(record, EvidenceRecord) for record in normalized):
            raise TypeError("evidence must contain only EvidenceRecord values")
        return normalized

    def step(
        self,
        state: EpistemicState,
        action: Action | None = None,
        evidence: Sequence[EvidenceRecord] = (),
    ) -> RuntimeStep:
        if not isinstance(state, EpistemicState):
            raise TypeError("state must be an EpistemicState")
        self._validate_action(action)
        normalized_evidence = self._normalize_evidence(evidence)
        before = state.normalized()
        selected = action if action is not None else self.choose(before)
        after = self.kernel.step(before, selected, normalized_evidence)
        return RuntimeStep(before=before, action=selected, after=after)

    def run(
        self,
        initial: EpistemicState,
        actions: Sequence[tuple[Action | None, Sequence[EvidenceRecord]]] = (),
    ) -> tuple[RuntimeStep, ...]:
        if not isinstance(initial, EpistemicState):
            raise TypeError("initial must be an EpistemicState")
        current = initial.normalized()
        steps: list[RuntimeStep] = []
        for item in actions:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("each runtime action must be a (Action | None, evidence) tuple")
            action, evidence = item
            result = self.step(current, action, evidence)
            steps.append(result)
            current = result.after
        return tuple(steps)
