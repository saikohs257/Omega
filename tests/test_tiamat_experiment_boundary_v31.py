import math
import pytest
from tiamat import IdentificationRunner, LockedModelEvaluator, STATE_SPACE
from tiamat.experiment_config import TemporalCausalGate, TournamentConfig
from tiamat.experiment_manifest import ExperimentManifest
from tiamat.metric_contract import ProbabilityContract, TargetProvenance

def _h(value: str) -> str: return value * 64

def test_config_rejects_markov_lag_above_hard_boundary():
    with pytest.raises(ValueError, match=r"\[1, 10\]"): TournamentConfig(max_markov_lag=11)

def test_causal_gate_rejects_lookback_above_hard_boundary():
    with pytest.raises(ValueError, match=r"\[1, 10\]"): TemporalCausalGate(max_lookback=11)

def test_manifest_requires_real_sha256_components():
    kwargs=dict(config_hash=_h("a"),corpus_hash=_h("b"),feature_provenance_hash=_h("c"),label_provenance_hash=_h("d"),model_registry_hash=_h("e"),probability_contract_hash=_h("f"),implementation_hash=_h("0"))
    assert len(ExperimentManifest(**kwargs).experiment_id)==64
    with pytest.raises(ValueError,match="SHA-256"): ExperimentManifest(**{**kwargs,"implementation_hash":"hello"})

def test_target_provenance_is_not_feature_provenance():
    payload=TargetProvenance("observed","mode-v1","observed controller mode",1.0,("mode",),_h("a")).to_dict()
    assert "target_dependencies" in payload and "label_feature_dependencies" not in payload

def test_probability_output_boundary_rejects_invalid_model_output():
    contract=ProbabilityContract(STATE_SPACE); row={"timestamp":"2026-08-08T10:00:00Z","B":0.2,"V":0.1,"D":0.0,"tau_D":0.0,"tau_mode":0.0,"mode":"Q"}
    def invalid(_row): return {state:(1.0 if state=="Q" else 0.0) for state in STATE_SPACE}|{"X":0.0}
    evaluator=LockedModelEvaluator("M3",IdentificationRunner(),invalid,contract)
    with pytest.raises(ValueError,match="state-space mismatch"): evaluator.evaluate([row])

def test_probability_output_boundary_rejects_nan():
    contract=ProbabilityContract(STATE_SPACE); row={"timestamp":"2026-08-08T10:00:00Z","B":0.2,"V":0.1,"D":0.0,"tau_D":0.0,"tau_mode":0.0,"mode":"Q"}
    def invalid(_row): return {state:(math.nan if state=="Q" else 0.0) for state in STATE_SPACE}
    evaluator=LockedModelEvaluator("M3",IdentificationRunner(),invalid,contract)
    with pytest.raises(ValueError,match="non-finite"): evaluator.evaluate([row])
