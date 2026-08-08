from typing import Mapping, Sequence
from .state import TiamatState
from .transition import transition

def replay(initial_state: TiamatState, evidence_sequence: Sequence[Mapping[str, object]]) -> TiamatState:
    state = initial_state
    for evidence in evidence_sequence:
        state = transition(state, evidence)
    return state
