import math
import pytest
from tiamat import TiamatMode, TiamatState, TiamatEngine, transition


def test_canonical_modes_include_refractory():
    assert set(TiamatMode) == {
        TiamatMode.QUIESCENT, TiamatMode.PRECURSOR, TiamatMode.EXCITATION,
        TiamatMode.COUPLED_TRANSFER, TiamatMode.HAZARD,
        TiamatMode.RELAXATION, TiamatMode.REFRACTORY,
    }


def test_m3_state_round_trip():
    state = TiamatState(B=.4, V=.1, D=.3, tau_D=5, tau_mode=2, mode=TiamatMode.EXCITATION)
    assert TiamatState.from_mapping(state.to_dict()) == state


def test_state_rejects_nonfinite_or_invalid_levels():
    with pytest.raises(ValueError):
        TiamatState(B=math.nan)
    with pytest.raises(ValueError):
        TiamatState(D=1.1)
    with pytest.raises(ValueError):
        TiamatState(tau_D=-1)


def test_derived_observables_are_not_primitives():
    state = TiamatState(B=.5, V=-.2, D=.4)
    assert state.recovery == .2
    assert state.momentum == -.2
    assert state.pressure == 0.0


def test_quiescent_to_precursor_to_excitation():
    state = transition(TiamatState(), {"V": .1})
    assert state.mode is TiamatMode.PRECURSOR
    state = transition(state, {"V": .1, "B": .2})
    assert state.mode is TiamatMode.EXCITATION


def test_hazard_and_refractory_paths_are_explicit():
    state = TiamatState(B=.4, V=.1, D=.9, mode=TiamatMode.RELAXATION)
    state = transition(state, {"damage_threshold": .8})
    assert state.mode is TiamatMode.HAZARD
    state = transition(TiamatState(B=.1, V=0.0, D=.2, mode=TiamatMode.RELAXATION), {"enter_refractory": True})
    assert state.mode is TiamatMode.REFRACTORY


def test_live_and_replay_share_transition_function():
    engine = TiamatEngine()
    initial = TiamatState()
    evidence = [{"V": .1}, {"V": .1, "B": .2}, {"D": .9, "damage_threshold": .8}]
    live = initial
    for item in evidence:
        live = engine.transition_state(live, item)
    assert engine.replay_state(initial, evidence) == live
