import math

import pytest

from tiamat.engine import TiamatEngine
from tiamat.guards import evaluate_guards
from tiamat.state import TiamatMode, TiamatState
from tiamat.transition import transition


def test_transition_rejects_out_of_range_evidence():
    with pytest.raises(ValueError):
        transition(TiamatState(), {"damage": 1.01})


def test_state_rejects_non_finite_values():
    with pytest.raises(ValueError):
        TiamatState(damage=math.nan)
    with pytest.raises(ValueError):
        TiamatState(excitation=math.inf)


def test_state_timers_are_immutable():
    state = TiamatState(timers={"x": 1})
    with pytest.raises(TypeError):
        state.timers["x"] = 2


def test_mapping_round_trip_is_canonical():
    state = TiamatState(mode=TiamatMode.EXCITED, damage=0.4, timers={"b": 2, "a": 1})
    assert TiamatState.from_mapping(state.to_dict()) == state


def test_residual_damage_during_relaxation_promotes_hazard():
    state = TiamatState(mode=TiamatMode.RELAXING, residual_load=0.2)
    next_state = transition(state, {"residual_threshold": 0.1})
    assert next_state.mode is TiamatMode.HAZARD


def test_excitation_expiration_enters_relaxation():
    state = TiamatState(excitation=0.5, timers={"excitation_age": 3})
    next_state = transition(state, {"excitation_duration": 3})
    assert next_state.mode is TiamatMode.RELAXING


def test_hazard_precedence_is_deterministic():
    state = TiamatState(excitation=0.5, damage=0.9)
    evidence = {"damage_threshold": 0.8, "excitation_duration": 1}
    assert transition(state, evidence).mode is TiamatMode.HAZARD


def test_promotion_guard_is_explicit():
    state = TiamatState(promotion_count=2)
    results = evaluate_guards(state, {"promotion_threshold": 2})
    assert any(r.name == "COUPLED_TRANSFER_HAZARD_PROMOTION" and r.triggered for r in results)


def test_engine_uses_same_transition_for_live_and_replay():
    engine = TiamatEngine()
    initial = TiamatState()
    evidence = [
        {"excitation": 0.6},
        {"damage": 0.9, "damage_threshold": 0.8},
    ]
    live = initial
    for item in evidence:
        live = engine.transition_state(live, item)
    restored = engine.replay_state(initial, evidence)
    assert live == restored
    assert restored.mode is TiamatMode.HAZARD
