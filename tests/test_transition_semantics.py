from __future__ import annotations

import pytest

from erk import Action
from erk.core import EpistemicState, EvidenceRecord, Transition


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


def test_duplicate_authority_grants_are_rejected() -> None:
    evidence = EvidenceRecord(
        evidence_id="e1",
        source="source",
        timestamp="2026-08-08T00:00:00Z",
        payload={},
        authority_grant=1,
        authority_grant_id="grant-1",
    )
    with pytest.raises(ValueError, match="duplicate authority grant id"):
        Transition.apply(
            EpistemicState(authority=0),
            Action.ESCALATE,
            evidence=(evidence, evidence),
            authorized_authority=1,
        )


def test_replayed_authority_grant_is_rejected() -> None:
    evidence = EvidenceRecord(
        evidence_id="e1",
        source="source",
        timestamp="2026-08-08T00:00:00Z",
        payload={},
        authority_grant=1,
        authority_grant_id="grant-1",
    )
    with pytest.raises(ValueError, match="authority grant replay"):
        Transition.apply(
            EpistemicState(authority=0, used_authority_grants=("grant-1",)),
            Action.ESCALATE,
            evidence=(evidence,),
            authorized_authority=1,
        )
