from tiamat.experiment_config import FeatureDeclaration, TemporalCausalGate, TournamentConfig
from tiamat.experiment_manifest import ExperimentManifest, corpus_fingerprint, provenance_fingerprint
from tiamat.identification_registry import registry_fingerprint
from tiamat.locked_evaluator import LockedModelEvaluator
from tiamat.metric_contract import LabelProvenance, ProbabilityContract


def _manifest_kwargs():
    return dict(
        config_hash="c",
        corpus_hash="d",
        feature_provenance_hash="f",
        label_provenance_hash="l",
        model_registry_hash=registry_fingerprint(),
        probability_contract_hash="p",
        implementation_hash="i",
    )


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
    base = _manifest_kwargs()
    experiment_id = ExperimentManifest(**base).experiment_id
    for key in base:
        changed = dict(base)
        changed[key] = changed[key] + "x"
        assert ExperimentManifest(**changed).experiment_id != experiment_id


def test_corpus_fingerprint_is_order_sensitive():
    assert corpus_fingerprint([{"t": 1}, {"t": 2}]) != corpus_fingerprint([{"t": 2}, {"t": 1}])


def test_probability_contract_rejects_invalid_distribution_without_repair():
    contract = ProbabilityContract(("Q", "P", "E"), sum_tolerance=1e-6)
    contract.validate({"Q": 0.2, "P": 0.3, "E": 0.5})
    for invalid in (
        {"Q": 0.2, "P": 0.3, "E": 0.4},
        {"Q": -0.1, "P": 0.5, "E": 0.6},
        {"Q": 0.2, "P": 0.3, "E": float("nan")},
    ):
        try:
            contract.validate(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid probability distribution was accepted")


def test_label_provenance_requires_declared_forward_exposure():
    label = LabelProvenance("proxy", "v1", "future transition within 6h", 0.9, ("B",), "corpus", 6)
    label.validate(max_declared_future_steps=10)
    try:
        label.validate(max_declared_future_steps=5)
    except ValueError:
        pass
    else:
        raise AssertionError("undeclared/excessive label horizon was accepted")


def test_label_boundary_requires_explicit_allowance():
    label = LabelProvenance("proxy", "v1", "episode outcome", 1.0, (), "corpus", 0, True)
    try:
        label.validate(max_declared_future_steps=10)
    except ValueError:
        pass
    else:
        raise AssertionError("episode-boundary label was accepted without allowance")


def test_provenance_hash_changes_when_label_temporal_exposure_changes():
    a = LabelProvenance("proxy", "v1", "transition", 1.0, (), "corpus", 1)
    b = LabelProvenance("proxy", "v1", "transition", 1.0, (), "corpus", 2)
    assert provenance_fingerprint(a.to_dict()) != provenance_fingerprint(b.to_dict())


def test_locked_evaluator_has_one_model_contract():
    evaluator = LockedModelEvaluator("M3", __import__("tiamat").IdentificationRunner())
    assert evaluator.model_id == "M3"
