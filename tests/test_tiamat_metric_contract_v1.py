import math

import pytest

from tiamat import ExperimentManifest, MetricContract, ProbabilityContract


def _metric():
    return MetricContract(ProbabilityContract(("Q", "P", "E")), ece_bins=10, log_floor=1e-15)


def _p(q, p, e):
    return {"Q": q, "P": p, "E": e}


def test_nll_definition_is_multiclass_negative_log_likelihood():
    metric = _metric()
    assert metric.nll(_p(0.8, 0.1, 0.1), "Q") == pytest.approx(-math.log(0.8))


def test_brier_definition_uses_full_state_space_squared_error():
    metric = _metric()
    assert metric.brier(_p(0.8, 0.1, 0.1), "Q") == pytest.approx((0.8-1.0)**2 + 0.1**2 + 0.1**2)


def test_ece_uses_fixed_width_confidence_bins():
    metric = _metric()
    rows = [(_p(0.9, 0.05, 0.05), "Q"), (_p(0.8, 0.1, 0.1), "P")]
    assert metric.ece(rows) == pytest.approx(0.5)


def test_metric_contract_rejects_invalid_probability_inputs():
    metric = _metric()
    with pytest.raises(ValueError):
        metric.nll({"Q": 0.5, "P": 0.5, "E": -0.0}, "Q")
    with pytest.raises(ValueError):
        metric.brier({"Q": 0.5, "P": 0.5, "E": 0.5}, "Q")


def test_metric_contract_is_serialized_as_identity_material():
    metric = _metric()
    payload = metric.to_dict()
    assert payload["version"] == "metric-contract-v1"
    assert payload["nll"]["log_floor"] == 1e-15
    assert payload["ece"]["bins"] == 10


def test_metric_definition_changes_experiment_identity():
    probability_hash = "a" * 64
    base = dict(config_hash="b"*64, corpus_hash="c"*64, feature_provenance_hash="d"*64, label_provenance_hash="e"*64, model_registry_hash="f"*64, probability_contract_hash=probability_hash, metric_contract_hash="1"*64, implementation_hash="2"*64)
    a = ExperimentManifest(**base).experiment_id
    b = ExperimentManifest(**{**base, "metric_contract_hash": "3"*64}).experiment_id
    assert a != b
