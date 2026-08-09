from __future__ import annotations

import pytest
from tiamat import HoldoutExperiment, IdentificationRunner, STATE_SPACE, TemporalCausalGate, TournamentConfig, TargetProvenance
from tiamat.experiment_manifest import corpus_fingerprint

ROWS = [
    {"timestamp":"2026-08-08T10:03:00Z","B":0.2,"V":0.1,"D":0.0,"tau_D":0.0,"tau_mode":0.0,"mode":"Q"},
    {"timestamp":"2026-08-08T10:01:00Z","B":0.0,"V":0.0,"D":0.0,"tau_D":0.0,"tau_mode":1.0,"mode":"Q"},
    {"timestamp":"2026-08-08T10:06:00Z","B":0.4,"V":-0.1,"D":0.3,"tau_D":3.0,"tau_mode":4.0,"mode":"R"},
    {"timestamp":"2026-08-08T10:02:00Z","B":0.1,"V":0.1,"D":0.0,"tau_D":0.0,"tau_mode":2.0,"mode":"P"},
    {"timestamp":"2026-08-08T10:05:00Z","B":0.5,"V":0.2,"D":0.4,"tau_D":4.0,"tau_mode":5.0,"mode":"H"},
    {"timestamp":"2026-08-08T10:04:00Z","B":0.3,"V":0.0,"D":0.2,"tau_D":2.0,"tau_mode":3.0,"mode":"C"},
]

def uniform_predictor(_row):
    p=1.0/len(STATE_SPACE); return {state:p for state in STATE_SPACE}

def _label_provenance() -> TargetProvenance:
    split=HoldoutExperiment().split_rows(ROWS)
    corpus_hash=corpus_fingerprint([r.to_mapping() for r in (*split.train,*split.validation,*split.test)])
    return TargetProvenance("observed","mode-v1","observed controller mode",1.0,("mode",),corpus_hash,0,False)

def test_holdout_split_orders_temporally_and_uses_all_rows() -> None:
    split=HoldoutExperiment().split_rows(ROWS)
    assert split.sizes=={"train":4,"validation":1,"test":1}
    assert [row.timestamp for row in split.train]==["2026-08-08T10:01:00Z","2026-08-08T10:02:00Z","2026-08-08T10:03:00Z","2026-08-08T10:04:00Z"]
    assert [row.timestamp for row in split.validation]==["2026-08-08T10:05:00Z"]
    assert [row.timestamp for row in split.test]==["2026-08-08T10:06:00Z"]

def test_holdout_evaluation_includes_frozen_experiment_identity_and_probability_preflight() -> None:
    implementation_hash="0"*64
    evaluation=IdentificationRunner().holdout_experiment(label_provenance=_label_provenance()).evaluate(ROWS,model_ids=("M0","M3","M7"),implementation_hash=implementation_hash,probability_predictor=uniform_predictor)
    payload=evaluation.to_dict()
    assert payload["version"]=="holdout-v3.1"
    assert payload["config"]["config_version"]=="tournament-config-v3.1"
    assert len(payload["config"]["config_hash"])==64
    assert len(payload["experiment_id"])==64
    assert payload["manifest"]["implementation_hash"]==implementation_hash
    assert payload["manifest"]["probability_contract_hash"]
    assert payload["probability_contract"]["violation_policy"]=="reject"
    assert payload["config"]["deferred_metrics"]==["transition_error","complexity","stability"]
    assert evaluation.selected_model_id in {"M0","M3","M7"}
    assert evaluation.locked_model_id==evaluation.selected_model_id
    assert evaluation.test_selected is not None

def test_holdout_requires_implementation_identity() -> None:
    with pytest.raises(ValueError,match="implementation_hash"):
        IdentificationRunner().holdout_experiment(label_provenance=_label_provenance()).evaluate(ROWS,model_ids=("M0",),probability_predictor=uniform_predictor)

def test_holdout_requires_probability_predictor() -> None:
    with pytest.raises(ValueError,match="probability_predictor"):
        IdentificationRunner().holdout_experiment(label_provenance=_label_provenance()).evaluate(ROWS,model_ids=("M0",),implementation_hash="0"*64)

def test_holdout_requires_label_provenance() -> None:
    with pytest.raises(ValueError,match="label_provenance"):
        IdentificationRunner().evaluate_holdout(ROWS,model_ids=("M0",),implementation_hash="0"*64,probability_predictor=uniform_predictor)

def test_causal_gate_rejects_future_contamination() -> None:
    gate=TemporalCausalGate(max_lookback=10)
    with pytest.raises(ValueError,match="temporal contamination"):
        gate.validate_row({"timestamp":"2026-08-08T10:00:00Z","B":0.2,"future_target":1})

def test_tournament_config_hash_is_deterministic() -> None:
    assert TournamentConfig().config_hash()==TournamentConfig().config_hash()
