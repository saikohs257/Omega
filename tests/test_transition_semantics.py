from __future__ import annotations

import pytest

from erk import Action
from erk.core import EpistemicState, Transition


def test_branch_increments_active_branches() -> None:
    state = EpistemicState(active_branches=1)
    after = Transition.apply(state, Action.BRANCH, branch_bound=2)
    assert after.active_branches == 2
    assert after.terminal is None


def test_branch_bound_is_enforced_at_transition_boundary() -> None:
    state = EpistemicState(active_branches=2)
    with pytest.raises(ValueError, match="branch bound"):
        Transition.apply(state, Action.BRANCH, branch_bound=2)


@pytest.mark.parametrize("action", [Action.REJECT, Action.QUARANTINE, Action.ARCHIVE])
def test_terminal_actions_are_terminal(action: Action) -> None:
    state = EpistemicState()
    after = Transition.apply(state, action)
    assert after.terminal == action.value
    with pytest.raises(ValueError, match="terminal branch"):
        Transition.apply(after, Action.BLOCK)


def test_execution_consumes_authority() -> None:
    state = EpistemicState(authority=2)
    after = Transition.apply(state, Action.ENABLE_EXECUTION)
    assert after.authority.value == 1
