from erk import Action, ConstitutionalRuntime, EpistemicState


def test_runtime_step_normalizes_state_and_records_transition() -> None:
    runtime = ConstitutionalRuntime()
    state = EpistemicState(observability={"signal": 2.0}, active_branches=-3)

    result = runtime.step(state, Action.BLOCK)

    assert result.before.observability["signal"] == 1.0
    assert result.before.active_branches == 0
    assert result.action is Action.BLOCK
    assert result.after == result.before


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
