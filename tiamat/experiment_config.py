from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from .experiment_manifest import canonical_hash
TOURNAMENT_CONFIG_VERSION="tournament-config-v3"
TEMPORAL_CAUSAL_GATE_VERSION="causal-gate-v3"
MAX_MARKOV_LAG=10
DEFAULT_METRIC_WEIGHTS=(("nll",1.0),("brier",1.0),("ece",1.0),("transition_error",1.0),("complexity",1.0),("stability",1.0))
DEFAULT_TIE_BREAK=("score","transition_error","coverage","complexity","model_id")
@dataclass(frozen=True,slots=True)
class TournamentConfig:
    metric_weights: tuple[tuple[str,float],...]=DEFAULT_METRIC_WEIGHTS
    split_boundaries: tuple[float,float,float]=(0.6,0.2,0.2)
    max_markov_lag:int=MAX_MARKOV_LAG
    complexity_definition:str="axis_count"
    stability_definition:str="innovation_autocorrelation_plus_parameter_stability"
    tie_break_policy:tuple[str,...]=DEFAULT_TIE_BREAK
    deterministic:bool=True
    telemetry_schema_version:str="tiamat.telemetry.v1"
    config_version:str=TOURNAMENT_CONFIG_VERSION
    def __post_init__(self)->None:
        weights=tuple(sorted((str(k),float(v)) for k,v in dict(self.metric_weights).items()))
        if any(v<0 or v!=v or v in (float("inf"),float("-inf")) for _,v in weights): raise ValueError("metric weights must be finite and non-negative")
        object.__setattr__(self,"metric_weights",weights); fractions=tuple(float(v) for v in self.split_boundaries)
        if len(fractions)!=3 or any(v<0 or v!=v or v in (float("inf"),float("-inf")) for v in fractions) or abs(sum(fractions)-1.0)>1e-9: raise ValueError("split_boundaries must be three finite non-negative values summing to 1.0")
        object.__setattr__(self,"split_boundaries",fractions); lag=int(self.max_markov_lag)
        if lag<1 or lag>MAX_MARKOV_LAG: raise ValueError(f"max_markov_lag must be in [1, {MAX_MARKOV_LAG}]")
        object.__setattr__(self,"max_markov_lag",lag); object.__setattr__(self,"tie_break_policy",tuple(str(v) for v in self.tie_break_policy))
    def canonical_payload(self)->dict[str,Any]: return {"config_version":self.config_version,"metric_weights":list(self.metric_weights),"split_boundaries":list(self.split_boundaries),"max_markov_lag":self.max_markov_lag,"complexity_definition":self.complexity_definition,"stability_definition":self.stability_definition,"tie_break_policy":list(self.tie_break_policy),"deterministic":self.deterministic,"telemetry_schema_version":self.telemetry_schema_version}
    def config_hash(self)->str: return canonical_hash(self.canonical_payload())
    def weights_dict(self)->dict[str,float]: return dict(self.metric_weights)
    def to_dict(self)->dict[str,Any]: return self.canonical_payload()|{"config_hash":self.config_hash()}
@dataclass(frozen=True,slots=True)
class FeatureDeclaration:
    name:str
    max_temporal_offset:int=0
    episode_boundary_aware:bool=False
    derived_from:tuple[str,...]=()
    def __post_init__(self)->None:
        if not self.name: raise ValueError("feature name is required")
        offset=int(self.max_temporal_offset)
        if offset<0: raise ValueError("feature temporal offset must be non-negative")
        object.__setattr__(self,"max_temporal_offset",offset); object.__setattr__(self,"derived_from",tuple(str(v) for v in self.derived_from))
@dataclass(frozen=True,slots=True)
class TemporalCausalGate:
    max_lookback:int=MAX_MARKOV_LAG
    features:tuple[FeatureDeclaration,...]=()
    gate_version:str=TEMPORAL_CAUSAL_GATE_VERSION
    def __post_init__(self)->None:
        lag=int(self.max_lookback)
        if lag<1 or lag>MAX_MARKOV_LAG: raise ValueError(f"max_lookback must be in [1, {MAX_MARKOV_LAG}]")
        object.__setattr__(self,"max_lookback",lag); object.__setattr__(self,"features",tuple(self.features))
    def feature_horizons(self)->dict[str,int]:
        declarations={f.name:f for f in self.features}; memo={}
        def horizon(name:str,trail:tuple[str,...]=())->int:
            if name in memo:return memo[name]
            if name in trail:raise ValueError(f"feature dependency cycle: {' -> '.join(trail+(name,))}")
            f=declarations.get(name)
            if f is None:raise ValueError(f"feature dependency is undeclared: {name}")
            if f.episode_boundary_aware:raise ValueError(f"feature uses eventual episode boundary: {name}")
            value=max([f.max_temporal_offset]+[horizon(p,trail+(name,)) for p in f.derived_from]); memo[name]=value; return value
        for name in declarations:horizon(name)
        return memo
    def validate_features(self)->None:
        horizons=self.feature_horizons(); violations={name:h for name,h in horizons.items() if h>self.max_lookback}
        if violations:raise ValueError(f"feature lookback exceeds Kmax={self.max_lookback}: {violations}")
    def validate_row(self,row:Mapping[str,Any])->None:
        forbidden=("episode_end","future_duration","future_target","next_target","target_t_plus_1")
        bad=[str(k) for k in row if str(k) in forbidden or str(k).startswith(("future_","next_","target_next_","y_next_")) or str(k).endswith(("_future","_next","_t+1"))]
        if bad: raise ValueError(f"temporal contamination detected: {', '.join(sorted(set(bad)))}")
        self.validate_features()
    def validate_rows(self,rows:Sequence[Mapping[str,Any]])->None:
        for row in rows:self.validate_row(row)
    def to_dict(self)->dict[str,Any]: return {"gate_version":self.gate_version,"max_lookback":self.max_lookback,"features":[{"name":f.name,"max_temporal_offset":f.max_temporal_offset,"episode_boundary_aware":f.episode_boundary_aware,"derived_from":list(f.derived_from)} for f in self.features]}
