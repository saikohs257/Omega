import math
import pytest
from tiamat.engine import TiamatEngine
from tiamat.guards import evaluate_guards
from tiamat.state import TiamatMode, TiamatState
from tiamat.transition import transition

def test_transition_rejects_out_of_range_evidence():
    with pytest.raises(ValueError): transition(TiamatState(), {"damage": 1.01})
def test_state_rejects_non_finite_values():
    with pytest.raises(ValueError): TiamatState(damage=math.nan)
    with pytest.raises(ValueError): TiamatState(excitation=math.inf)
def test_state_round_trip_is_canonical():
    state=TiamatState(mode=TiamatMode.EXCITED, excitation=.4, damage=.3, recovery=.2, residual_load=.1, momentum=.5, mode_age_h=4, excitation_age_h=3, refractory_age_h=2, promotion_count=1, arrival_class="PULLBACK", hysteresis_memory=("EXCITED",))
    assert TiamatState.from_mapping(state.to_dict()) == state
def test_residual_damage_during_relaxation_promotes_hazard():
    state=TiamatState(mode=TiamatMode.RELAXING,residual_load=.2)
    assert transition(state,{"residual_threshold":.1}).mode is TiamatMode.HAZARD
def test_excitation_expiration_enters_relaxation():
    state=TiamatState(excitation=.5,excitation_age_h=3)
    assert transition(state,{"excitation_duration":3}).mode is TiamatMode.RELAXING
def test_hazard_precedence_is_deterministic():
    state=TiamatState(excitation=.5,damage=.9)
    assert transition(state,{"damage_threshold":.8,"excitation_duration":1}).mode is TiamatMode.HAZARD
def test_promotion_guard_is_explicit():
    results=evaluate_guards(TiamatState(promotion_count=2),{"promotion_threshold":2})
    assert any(r.name=="COUPLED_TRANSFER_HAZARD_PROMOTION" and r.triggered for r in results)
def test_engine_uses_same_transition_for_live_and_replay():
    engine=TiamatEngine(); initial=TiamatState(); evidence=[{"excitation":.6},{"damage":.9,"damage_threshold":.8}]
    live=initial
    for item in evidence: live=engine.transition_state(live,item)
    restored=engine.replay_state(initial,evidence)
    assert live==restored
    assert restored.mode is TiamatMode.HAZARD
