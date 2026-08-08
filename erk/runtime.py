from __future__ import annotations

from dataclasses import dataclass, field, replace
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
        return self.kernel.supervisor.supervise(state)
    def _facade_normalize(self, state: EpistemicState) -> EpistemicState:
        # The public facade may repair legacy malformed counters at its boundary;
        # the canonical EpistemicState.normalized() contract remains strict.
        if state.active_branches < 0:
            state = replace(state, active_branches=0)
        return state.normalized()
    def step(self,state:EpistemicState,action:Action|None=None,evidence:Sequence[EvidenceRecord]=()):
        before=self._facade_normalize(state)
        selected=action if action is not None else self.choose(before)
        after=self.kernel.step(before,selected,tuple(evidence))
        return RuntimeStep(before=before,action=selected,after=after)
    def run(self,initial:EpistemicState,actions:Sequence[tuple[Action|None,Sequence[EvidenceRecord]]]=()):
        current=self._facade_normalize(initial); steps=[]
        for action,evidence in actions:
            result=self.step(current,action,evidence); steps.append(result); current=result.after
        return tuple(steps)
