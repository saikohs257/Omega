import pytest

from erk import Action, ConstitutionalRuntime, EpistemicState, EvidenceRecord


def test_runtime_step_rejects_negative_state_counters() -> None:
    runtime = ConstitutionalRuntime()
    state = EpistemicState(observability={"signal": 2.0}, active_branches=-3)

    with pytest.raises(ValueError, match="active_branches must be non-negative"):
        runtime.step(state, Action.BLOCK)


def test_runtime_step_chooses_constitutional_action_when_omitted() -> None:
    runtime = ConstitutionalRuntime()
    state = EpistemicState()

    result = runtime.step(state)

    assert result.action is Action.BLOCK
    assert result.after == result.before


def test_runtime_run_chains_previous_state_into_next_step() -> None:
    runtime = ConstitutionalRuntime()
    initial = EpistemicState()

    steps = runtime.run(
        initial,
        (
            (Action.BRANCH, ()),
            (Action.ARCHIVE, ()),
        ),
    )

    assert len(steps) == 2
    assert steps[0].before == initial
    assert steps[0].after.active_branches == 2
    assert steps[1].before == steps[0].after
    assert steps[1].action is Action.ARCHIVE
    assert steps[1].after.terminal == Action.ARCHIVE.value


def test_runtime_step_rejects_non_action_values() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="action must be an Action or None"):
        runtime.step(EpistemicState(), "BLOCK")  # type: ignore[arg-type]


def test_runtime_step_rejects_non_evidence_values() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="evidence must contain only EvidenceRecord values"):
        runtime.step(EpistemicState(), Action.BLOCK, (object(),))  # type: ignore[arg-type]


def test_runtime_run_rejects_malformed_action_entries() -> None:
    runtime = ConstitutionalRuntime()

    with pytest.raises(TypeError, match="each runtime action must be a"):
        runtime.run(EpistemicState(), ((Action.BLOCK,),))  # type: ignore[arg-type]


def test_runtime_step_accepts_evidence_records() -> None:
    runtime = ConstitutionalRuntime()
    evidence = EvidenceRecord(
        evidence_id="evidence-1",
        source="test",
        timestamp="2026-08-08T12:00:00Z",
        payload={"signal": "stable"},
    )

    result = runtime.step(EpistemicState(), Action.BLOCK, (evidence,))

    assert result.after.evidence_count == 1
