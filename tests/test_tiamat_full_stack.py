import math

from tiamat import (
    TiamatEngine,
    TiamatMode,
    TiamatState,
    hazard_score,
    live_deficit_update,
    residual_load,
    sigmoid,
    simple_shock,
)


def test_full_dynamics_surface_is_deterministic_and_bounded() -> None:
    medians = (0.1, 0.2, 0.3, 0.4, 0.5)
    mads = (0.1, 0.1, 0.1, 0.1, 0.1)
    shock_a = simple_shock(
        abs_ret=0.2,
        rv24=0.3,
        range_pct=0.4,
        log_qv=0.5,
        imb_abs=0.6,
        medians=medians,
        mads=mads,
    )
    shock_b = simple_shock(
        abs_ret=0.2,
        rv24=0.3,
        range_pct=0.4,
        log_qv=0.5,
        imb_abs=0.6,
        medians=medians,
        mads=mads,
    )
    assert shock_a == shock_b
    assert 0.0 < shock_a < 1.0
    deficit = live_deficit_update(0.5, -1.0, shock_a, 0.0)
    assert 0.0 < deficit < 1.0
    assert math.isclose(residual_load(0.8, 0.2), 0.6, rel_tol=0.0, abs_tol=1e-12)
    assert 0.0 < hazard_score(2.0) < 1.0


def test_full_engine_step_and_diagnose_share_one_transition() -> None:
    engine = TiamatEngine()
    initial = TiamatState()
    evidence = {"V": 0.2, "B": 0.3, "D": 0.1, "hazard_raw": 0.4, "path": "arc"}
    stepped = engine.step(initial, evidence)
    diagnostic = engine.diagnose(initial, evidence)
    assert diagnostic["state"] == stepped.to_dict()
    assert diagnostic["observables"]["momentum"] == stepped.momentum
    assert diagnostic["context"]["path"] == "arc"


def test_engine_evaluate_uses_real_tiamat_transition_for_state_requests() -> None:
    engine = TiamatEngine()
    decision = engine.evaluate(
        TiamatState().to_dict(),
        {"V": 0.1},
    )
    assert decision.approved is True
    assert decision.state["mode"] == TiamatMode.PRECURSOR.value
    assert decision.event.kind == "tiamat_transition"


def test_engine_replay_matches_repeated_steps() -> None:
    engine = TiamatEngine()
    initial = TiamatState()
    evidence = (
        {"V": 0.1},
        {"V": 0.1, "B": 0.2},
        {"D": 0.9, "damage_threshold": 0.8},
    )
    state = initial
    for row in evidence:
        state = engine.step(state, row)
    assert engine.replay_state(initial, evidence) == state
    assert math.isfinite(state.residual_load)


def test_diagnose_accepts_canonical_state_for_matched_damage_pokes() -> None:
    engine = TiamatEngine()
    evidence = {"B": 0.0, "V": 1.0, "D": 0.0}
    for damage in (0.0, 1e-9, 1e-6):
        state = TiamatState(B=0.0, V=1.0, D=damage)
        diagnostic = engine.diagnose(state, evidence)
        assert diagnostic["state"]["D"] == damage
        assert diagnostic["state"]["V"] == 1.0
        assert diagnostic["state"]["B"] == 0.0
