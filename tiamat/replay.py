from __future__ import annotations

from typing import Any, Mapping, Sequence

from .state import TiamatState
from .transition import transition


def replay(initial_state: TiamatState, evidence_sequence: Sequence[Mapping[str, Any]]) -> TiamatState:
    """Reconstruct TIAMAT using the exact live transition function."""
    state = initial_state
    for evidence in evidence_sequence:
        state = transition(state, evidence)
    return state
