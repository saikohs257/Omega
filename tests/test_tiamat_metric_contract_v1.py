import math

import pytest

from tiamat import ExperimentManifest, MetricContract, ProbabilityContract


def _metric(**kwargs):
    return MetricContract(ProbabilityContract(("Q", "P", "E")), **kwargs)


def _p(q, p, e):
    return {"Q": q, "P": p, "E": e}


def test_nll_definition_and_frozen_zero_clip():
    metric = _metric()
    assert metric.nll(_p(0.8, 0.1, 0.1), "Q") == pytest.approx(-math.log(0.8))
    assert metric.nll(_p(0.0, 0.5, 0.5), "Q") == pytest.approx(-math.log(1e-10))
    assert metric.nll_zero_clip == 1e-10


def test_brier_uses_frozen_sum_convention():
    metric = _metric()
    expected = (0.8 - 1.0) ** 2 + 0.1**2 + 0.1**2
    assert metric.brier(_p(0.8, 0.1, 0.1), "Q") == pytest.approx(expected)
    assert metric.brier_convention == "sum"


def test_brier_mean_convention_is_explicit_and_distinct():
    metric = _metric(brier_convention="mean")
    assert metric.brier(_p(0.8, 0.1, 0.1), "Q") == pytest.approx(((0.8 - 1.0) ** 2 + 0.1**2 + 0.1**2) / 3)


def test_ece_uses_frozen_bins_and_max_probability():
    metric = _metric(ece_bins=10)
    rows = [(_p(0.9, 0.05, 0.05), "Q"), (_p(0.8, 0.1, 0.1), "P")]
    assert metric.ece(rows) == pytest.approx(0.45)
    assert metric.ece_confidence == "max_probability"
    assert metric.ece_bins == 10


def test_ece_true_state_probability_is_explicit_alternative():
    metric = _metric(ece_confidence="true_state_probability")
    rows = [(_p(0.9, 0.05, 0.05), "Q"), (_p(0.8, 0.1, 0.1), "P")]
    assert metric.ece(rows) == pytest.approx(0.45)


def test_perfect_predictor_has_zero_proper_scores_and_ece():
    metric = _metric()
    rows = [(_p(1.0, 0.0, 0.0), "Q"), (_p(0.0, 1.0, 0.0), "P"), (_p(0.0, 0.0, 1.0), "E")]
    scores = metric.score(rows)
    assert scores["nll"] == pytest.approx(0.0)
    assert scores["brier"] == pytest.approx(0.0)
    assert scores["ece"] == pytest.approx(0.0)


def test_uniform_predictor_has_known_nll_brier_and_calibrated_ece():
    metric = _metric()
    uniform = _p(1 / 3, 1 / 3, 1 / 3)
    rows = [(uniform, "Q"), (uniform, "P"), (uniform, "E")]
    scores = metric.score(rows)
    assert scores["nll"] == pytest.approx(math.log(3))
    assert scores["brier"] == pytest.approx(2 / 3)
    assert scores["ece"] == pytest.approx(0.0)


def test_metric_contract_rejects_invalid_probability_inputs():
    metric = _metric()
    with pytest.raises(ValueError):
        metric.nll({"Q": 0.5, "P": 0.5, "E": -0.1}, "Q")
    with pytest.raises(ValueError):
        metric.brier({"Q": 0.5, "P": 0.5, "E": 0.5}, "Q")


def test_metric_contract_is_serialized_as_identity_material():
    metric = _metric()
    payload = metric.to_dict()
    assert payload["version"] == "metric-contract-v1.1"
    assert payload["nll"]["zero_clip"] == 1e-10
    assert payload["brier"]["convention"] == "sum"
    assert payload["ece"]["bins"] == 10
    assert payload["ece"]["confidence"] == "max_probability"
    assert payload["aggregation"]["level"] == "timestep"


def test_metric_contract_rejects_invalid_frozen_choices():
    probability = ProbabilityContract(("Q", "P", "E"))
    with pytest.raises(ValueError):
        MetricContract(probability, brier_convention="other")
    with pytest.raises(ValueError):
        MetricContract(probability, ece_confidence="other")
    with pytest.raises(ValueError):
        MetricContract(probability, aggregation_level="row")


def test_metric_definition_changes_experiment_identity():
    probability_hash = "a" * 64
    base = dict(
        config_hash="b" * 64,
        corpus_hash="c" * 64,
        feature_provenance_hash="d" * 64,
        label_provenance_hash="e" * 64,
        model_registry_hash="f" * 64,
        probability_contract_hash=probability_hash,
        metric_contract_hash="1" * 64,
        implementation_hash="2" * 64,
    )
    a = ExperimentManifest(**base).experiment_id
    b = ExperimentManifest(**{**base, "metric_contract_hash": "3" * 64}).experiment_id
    assert a != b
