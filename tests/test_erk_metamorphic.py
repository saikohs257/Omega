from __future__ import annotations

from erk import Action, Authority, ConstitutionalKernel, EpistemicState, EvidenceRecord
from erk.core import state_hash


def test_reordering_independent_evidence_does_not_change_state_hash() -> None:
    kernel = ConstitutionalKernel()
    e1 = EvidenceRecord("e1", "trusted", "t1", {"x": 1})
    e2 = EvidenceRecord("e2", "trusted", "t2", {"y": 2})
    a = kernel.replay(EpistemicState(), ((Action.BRANCH, (e1, e2)),))[-1]
    b = kernel.replay(EpistemicState(), ((Action.BRANCH, (e2, e1)),))[-1]
    assert state_hash(a) == state_hash(b)


def test_irrelevant_prose_is_not_runtime_state() -> None:
    kernel = ConstitutionalKernel()
    a = kernel.step(EpistemicState(authority=Authority.SIMULATE), Action.BRANCH)
    b = kernel.step(EpistemicState(authority=Authority.SIMULATE), Action.BRANCH)
    assert state_hash(a) == state_hash(b)
