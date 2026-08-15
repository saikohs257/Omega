from pytest import approx

from hydra import HydraEngine, HydraEvidence, HydraState
from hydra.modules import BurdenModule, HazardModule, LaneCoordinator, PersistenceModule, RecoveryModule, TrajectoryModule


def ev(hazard: float, burden: float, shock: float = 0.0, recovery_weakness: float = 0.0, age: int = 0, prev_ld=None):
    return HydraEvidence(
        hazard_raw=hazard * 10.0,
        hazard_score=hazard,
        live_deficit=burden,
        simple_shock=shock,
        recovery_weakness=recovery_weakness,
        episode_age_h=age,
        prev_live_deficit=prev_ld,
    )


def test_lane_boundary_edges_and_extremes():
    r = LaneCoordinator()
    assert r.route(-1.0) == "0_to_4"
    assert r.route(0.70) == "0_to_4"
    assert r.route(0.7000001) == "2_to_4"
    assert r.route(0.85) == "2_to_4"
    assert r.route(0.8500001) == "3_to_4"
    assert r.route(2.0) == "3_to_4"


def test_sensor_outputs_are_bounded():
    state = HydraState()
    evidence = ev(3.0, -2.0, recovery_weakness=4.0)
    scores = [
        HazardModule().update(evidence, state),
        BurdenModule().update(evidence, state),
        RecoveryModule().update(evidence, state),
        TrajectoryModule().update(evidence, state),
        PersistenceModule().update(evidence, state),
    ]
    assert all(0.0 <= x <= 1.0 for x in scores)


def test_hazard_monotonicity():
    m = HazardModule()
    s = HydraState()
    assert m.update(ev(0.2, 0.5), s) <= m.update(ev(0.8, 0.5), s)


def test_burden_monotonicity():
    m = BurdenModule()
    s = HydraState()
    assert m.update(ev(0.5, 0.2), s) <= m.update(ev(0.5, 0.8), s)


def test_recovery_capacity_is_inverse_of_weakness():
    m = RecoveryModule()
    s = HydraState()
    low = m.update(ev(0.5, 0.5, recovery_weakness=0.1), s)
    high = m.update(ev(0.5, 0.5, recovery_weakness=0.9), s)
    assert 0.0 <= high < low <= 1.0


def test_trajectory_direction_from_hazard_change():
    m = TrajectoryModule()
    assert m.update(ev(0.8, 0.5), HydraState(hazard=0.2)) == approx(0.8)
    assert m.update(ev(0.2, 0.5), HydraState(hazard=0.8)) == approx(0.2)
    assert m.update(ev(0.5, 0.5), HydraState(hazard=0.5)) == approx(0.5)


def test_persistence_saturates_at_24_hours():
    m = PersistenceModule()
    s = HydraState()
    assert m.update(ev(0.5, 0.5, age=0), s) == 0.0
    assert m.update(ev(0.5, 0.5, age=12), s) == 0.5
    assert m.update(ev(0.5, 0.5, age=24), s) == 1.0
    assert m.update(ev(0.5, 0.5, age=240), s) == 1.0


def test_lane_scores_are_bounded_for_all_known_paths():
    r = LaneCoordinator()
    for path in ("0_to_4", "2_to_4", "3_to_4", "unknown"):
        score = r.score(path, 1.0, 1.0, 0.0, 1.0)
        assert 0.0 <= score <= 1.0


def test_engine_preserves_disagreement_and_provenance():
    d = HydraEngine().step(HydraState(), ev(0.9, 0.75, shock=0.8, recovery_weakness=0.8, age=6, prev_ld=0.75))
    assert d.state.entry_path == "2_to_4"
    assert set(d.disagreements) == {
        "hazard_vs_burden",
        "burden_vs_recovery_failure",
        "hazard_vs_trajectory",
    }
    assert all(v >= 0.0 for v in d.disagreements.values())
    assert d.module_scores["lane"] == d.state.lane_scores["2_to_4"]


def test_replay_is_deterministic_and_stateful():
    rows = [
        ev(0.4, 0.3, prev_ld=0.3),
        ev(0.6, 0.5, prev_ld=0.3, age=1),
        # Cross the documented lane boundary so the final replay path is 2_to_4.
        ev(0.8, 0.7, prev_ld=0.7000001, age=2),
    ]
    engine = HydraEngine()
    a = engine.replay(rows)
    b = engine.replay(rows)
    assert a == b
    assert a[-1].state.persistence == 2
    assert a[-1].state.entry_path == "2_to_4"


def test_normal_conditions_stay_noncatastrophic():
    d = HydraEngine().step(HydraState(), ev(0.2, 0.2, recovery_weakness=0.1))
    assert d.action in {"NORMAL", "STRESSED"}
    assert d.action not in {"RECOVERY_FAILURE", "TRANSITION_RISK"}


def test_recovery_failure_is_explicit_when_burden_and_weak_recovery_are_high():
    d = HydraEngine().step(HydraState(), ev(0.9, 0.9, recovery_weakness=0.9))
    assert d.action == "RECOVERY_FAILURE"


def test_transition_risk_requires_rising_trajectory_and_hazard():
    d = HydraEngine().step(HydraState(hazard=0.2), ev(0.95, 0.4, recovery_weakness=0.1))
    assert d.module_scores["trajectory"] > 0.6
    assert d.action in {"TRANSITION_RISK", "STRESSED", "PERSISTENT_STRESS"}


def test_negative_and_oversized_inputs_are_clamped_not_crashing():
    d = HydraEngine().step(HydraState(), ev(-5.0, 9.0, recovery_weakness=-3.0, age=-20))
    assert all(0.0 <= v <= 1.0 for k, v in d.module_scores.items() if k != "lane")
    assert d.state.persistence == 0
