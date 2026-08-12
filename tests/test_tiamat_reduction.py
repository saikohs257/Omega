from tiamat.identification_registry import MODEL_REGISTRY
from tiamat.modes import TiamatMode
from tiamat.reduction import ReducedState, replay_shadow, replay_transition_shadow
from tiamat.state import TiamatState


def test_reduced_state_contains_only_d_v_q_tau() -> None:
    state = TiamatState(D=0.7, V=-0.2, tau_mode=4.0, mode=TiamatMode.RELAXATION)
    reduced = ReducedState.from_state(state)
    assert reduced.to_dict() == {
        "D": 0.7,
        "V": -0.2,
        "q": TiamatMode.RELAXATION.value,
        "tau": 4.0,
    }


def test_m8_registry_is_explicitly_minimal_and_does_not_replace_m3() -> None:
    assert MODEL_REGISTRY["M8"].state == ("D", "V", "tau_mode", "mode")
    assert MODEL_REGISTRY["M8"].role == "explicit D,V,q,tau shadow candidate"
    assert MODEL_REGISTRY["M3"].state == ("B", "V", "D")


def test_shadow_replay_is_observational_and_does_not_change_canonical_modes() -> None:
    rows = (
        {"timestamp": "t0", "D": 0.1, "V": 0.0, "mode": TiamatMode.QUIESCENT.value},
        {"timestamp": "t1", "D": 0.2, "V": 0.2, "mode": TiamatMode.PRECURSOR.value},
        {"timestamp": "t2", "D": 0.3, "V": 0.3, "mode": TiamatMode.EXCITATION.value},
    )
    result = replay_shadow(rows)
    assert result.agreement_rate == 1.0
    assert result.disagreements == ()
    assert result.rows[-1].full_transition == "P->E"
    assert result.rows[-1].reduced_transition == "P->E"


def test_transition_shadow_exposes_only_reduced_state() -> None:
    states = replay_transition_shadow(
        TiamatState(),
        ({"V": 0.1}, {"V": 0.1, "B": 0.2}),
    )
    assert [state.q for state in states] == [
        TiamatMode.PRECURSOR.value,
        TiamatMode.EXCITATION.value,
    ]
    assert all(set(state.to_dict()) == {"D", "V", "q", "tau"} for state in states)
