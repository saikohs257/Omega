from tiamat.guards import evaluate_guards
from tiamat.replay import replay
from tiamat.state import TiamatMode, TiamatState
from tiamat.transition import transition


def test_state_is_bounded_and_serializable():
    state = TiamatState(damage=0.4, recovery=0.2, residual_load=0.3, excitation=0.1)
    payload = state.to_dict()
    assert payload["mode"] == TiamatMode.IDLE.value
    assert payload["damage"] == 0.4


def test_hazard_guard_is_deterministic():
    state = TiamatState(damage=0.9)
    evidence = {"damage_threshold": 0.8}
    assert evaluate_guards(state, evidence) == evaluate_guards(state, evidence)
    assert any(g.name == "DURATION_DAMAGE_HAZARD_GUARD" and g.triggered for g in evaluate_guards(state, evidence))


def test_live_transition_equals_replay():
    initial = TiamatState()
    evidence = [
        {"excitation": 1.0},
        {"damage_threshold": 0.8, "damage": 0.9},
    ]
    live = initial
    for item in evidence:
        if "damage" in item:
            live = TiamatState(damage=item["damage"], excitation=live.excitation)
        live = transition(live, item)
    restored = replay(initial, evidence)
    assert restored == replay(initial, evidence)
    assert restored.mode == TiamatMode.HAZARD


def test_invalid_state_values_are_rejected():
    try:
        TiamatState(damage=1.1)
    except ValueError:
        return
    raise AssertionError("out-of-range damage must be rejected")
