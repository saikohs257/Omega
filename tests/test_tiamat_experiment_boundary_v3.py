from tiamat.experiment_config import FeatureDeclaration, TemporalCausalGate, TournamentConfig
from tiamat.experiment_manifest import ExperimentManifest, corpus_fingerprint
from tiamat.identification_registry import registry_fingerprint
from tiamat.locked_evaluator import LockedModelEvaluator


def test_config_is_immutable_and_hash_changes_with_policy():
    a = TournamentConfig(metric_weights=(("nll", 1.0),))
    b = TournamentConfig(metric_weights=(("nll", 0.0),))
    assert a.config_hash() != b.config_hash()
    try:
        a.metric_weights += (("x", 1.0),)
    except Exception:
        pass
    else:
        raise AssertionError("frozen tournament config was mutable")


def test_feature_dag_enforces_bounded_causal_horizon():
    gate = TemporalCausalGate(max_lookback=10, features=(
        FeatureDeclaration("base", 0),
        FeatureDeclaration("lagged", 11, derived_from=("base",)),
    ))
    try:
        gate.validate_features()
    except ValueError as exc:
        assert "Kmax=10" in str(exc)
    else:
        raise AssertionError("lookback > Kmax was accepted")


def test_feature_dag_rejects_episode_boundary_dependency():
    gate = TemporalCausalGate(features=(FeatureDeclaration("duration", 0, episode_boundary_aware=True),))
    try:
        gate.validate_features()
    except ValueError as exc:
        assert "episode boundary" in str(exc)
    else:
        raise AssertionError("episode-boundary feature was accepted")


def test_experiment_identity_changes_with_any_manifest_component():
    base = dict(config_hash="c", corpus_hash="d", model_registry_hash=registry_fingerprint(), implementation_hash="i")
    a = ExperimentManifest(**base).experiment_id
    for key in ("config_hash", "corpus_hash", "model_registry_hash", "implementation_hash"):
        changed = dict(base)
        changed[key] = changed[key] + "x"
        assert ExperimentManifest(**changed).experiment_id != a


def test_corpus_fingerprint_is_order_sensitive():
    assert corpus_fingerprint([{"t": 1}, {"t": 2}]) != corpus_fingerprint([{"t": 2}, {"t": 1}])


def test_locked_evaluator_has_one_model_contract():
    evaluator = LockedModelEvaluator("M3", __import__("tiamat").IdentificationRunner())
    assert evaluator.model_id == "M3"
