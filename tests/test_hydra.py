from hydra import HydraEngine, HydraEvidence, HydraState
from hydra.modules import LaneCoordinator, TrajectoryModule


def test_lane_routing_matches_recovered_partition() -> None:
    router = LaneCoordinator()
    assert router.route(0.70) == "0_to_4"
    assert router.route(0.7001) == "2_to_4"
    assert router.route(0.85) == "2_to_4"
    assert router.route(0.8501) == "3_to_4"
    assert router.route(None) == "unknown"


def test_trajectory_uses_normalized_hazard_scale() -> None:
    module = TrajectoryModule()
    state = HydraState(hazard=0.40)
    evidence = HydraEvidence(
        hazard_raw=8.0,
        hazard_score=0.80,
        live_deficit=0.60,
        simple_shock=0.40,
        recovery_weakness=0.40,
    )
    assert module.update(evidence, state) == 0.70


def test_hydra_preserves_module_disagreement() -> None:
    engine = HydraEngine()
    decision = engine.step(
        HydraState(),
        HydraEvidence(
            hazard_raw=3.0,
            hazard_score=0.90,
            live_deficit=0.75,
            simple_shock=0.60,
            recovery_weakness=0.80,
            prev_live_deficit=0.75,
            episode_age_h=6,
        ),
    )
    assert decision.state.entry_path == "2_to_4"
    assert "hazard_vs_burden" in decision.disagreements
    assert decision.module_votes["lane"] == "2_to_4"


def test_replay_is_deterministic() -> None:
    rows = [
        HydraEvidence(2.0, 0.70, 0.50, 0.40, 0.30),
        HydraEvidence(2.2, 0.78, 0.58, 0.55, 0.40, prev_live_deficit=0.50),
        HydraEvidence(2.5, 0.84, 0.68, 0.65, 0.55, prev_live_deficit=0.58, episode_age_h=2),
    ]
    engine = HydraEngine()
    assert engine.replay(rows) == engine.replay(rows)
