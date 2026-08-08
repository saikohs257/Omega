import pytest

from erk import Action, ConstitutionalRuntime, EpistemicState


def test_runtime_selects_and_replays_deterministically() -> None:
    runtime = ConstitutionalRuntime()
    initial = EpistemicState()

    first = runtime.step(initial)
    second = runtime.step(initial)

    assert first.action == Action.BLOCK
    assert first == second
    assert first.before == initial.normalized()
    assert first.after.evidence_count == 0


def test_runtime_preserves_explicit_action_sequence() -> None:
    runtime = ConstitutionalRuntime()
    initial = EpistemicState()

    steps = runtime.run(initial, ((Action.BRANCH, ()), (Action.BLOCK, ())))

    assert [step.action for step in steps] == [Action.BRANCH, Action.BLOCK]
    assert steps[0].after.active_branches == 2
    assert steps[1].before == steps[0].after


def test_runtime_rejects_non_sequence_evidence() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="evidence must be a sequence"):
        runtime.step(EpistemicState(), evidence=object())  # type: ignore[arg-type]


def test_runtime_rejects_non_sequence_actions() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="actions must be a sequence"):
        runtime.run(EpistemicState(), actions=None)  # type: ignore[arg-type]


def test_runtime_rejects_malformed_action_entries_before_execution() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="each runtime action"):
        runtime.run(EpistemicState(), actions=((Action.BLOCK,),))  # type: ignore[arg-type]
