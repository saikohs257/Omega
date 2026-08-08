from __future__ import annotations

from dataclasses import dataclass, field
import math
from statistics import fmean
from typing import Any, Callable, Mapping, Sequence
from .experiment_config import TournamentConfig
from .identification_registry import MODEL_REGISTRY
from .metric_contract import ProbabilityPredictor
from .state import TiamatState
from .telemetry import CANONICAL_CONTROL_AXES, TelemetryAdapter, TelemetryRow, axes_for_model
from .transition import transition

TransitionFn = Callable[[TiamatState, Mapping[str, Any]], TiamatState]

@dataclass(frozen=True, slots=True)
class CandidateTrial:
    model_id: str
    role: str
    axes: tuple[str, ...]
    rows: int
    supported_rows: int
    coverage: float
    transition_error: float | None
    complexity: int
    is_control: bool = False
    @property
    def score(self) -> float:
        penalty = self.transition_error if self.transition_error is not None else 0.0
        return self.coverage - penalty - 0.01 * self.complexity

@dataclass(frozen=True, slots=True)
class TournamentReport:
    trials: tuple[CandidateTrial, ...]
    @property
    def winner(self) -> CandidateTrial | None: return self.trials[0] if self.trials else None

@dataclass(frozen=True, slots=True)
class IdentificationRunner:
    """Deterministic laboratory runner; legacy transition score remains a control metric."""
    adapter: TelemetryAdapter = field(default_factory=TelemetryAdapter)
    transition_fn: TransitionFn = transition
    control_model_id: str = "M7"
    control_axes: tuple[str, ...] = CANONICAL_CONTROL_AXES
    def normalize_rows(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_id: str = "M3") -> tuple[TelemetryRow, ...]: return tuple(self.adapter.normalize(row, model_id=model_id) for row in rows)
    def axes_for(self, model_id: str) -> tuple[str, ...]: return self.control_axes if model_id == self.control_model_id else axes_for_model(model_id)
    def evaluate(self, rows: Sequence[Mapping[str, Any] | TelemetryRow], *, model_ids: Sequence[str] | None = None) -> TournamentReport:
        normalized=self.normalize_rows(rows); ids=tuple(model_ids or MODEL_REGISTRY.keys()); return TournamentReport(tuple(sorted((self._evaluate_model(normalized,m) for m in ids),key=self._trial_order)))
    def holdout_experiment(self, *, train_fraction: float=0.6, validation_fraction: float=0.2, test_fraction: float=0.2, config: TournamentConfig|None=None, implementation_hash: str|None=None, probability_predictor: ProbabilityPredictor|None=None):
        from .holdout import HoldoutExperiment
        return HoldoutExperiment(runner=self, train_fraction=train_fraction, validation_fraction=validation_fraction, test_fraction=test_fraction, adapter=self.adapter, config=config, implementation_hash=implementation_hash or "UNBOUND", probability_predictor=probability_predictor)
    def split_rows(self, rows: Sequence[Mapping[str, Any]|TelemetryRow], *, train_fraction: float=0.6, validation_fraction: float=0.2, test_fraction: float=0.2, config: TournamentConfig|None=None): return self.holdout_experiment(train_fraction=train_fraction,validation_fraction=validation_fraction,test_fraction=test_fraction,config=config).split_rows(rows)
    def evaluate_holdout(self, rows: Sequence[Mapping[str, Any]|TelemetryRow], *, model_ids: Sequence[str]|None=None, train_fraction: float=0.6, validation_fraction: float=0.2, test_fraction: float=0.2, config: TournamentConfig|None=None, implementation_hash: str|None=None, probability_predictor: ProbabilityPredictor|None=None): return self.holdout_experiment(train_fraction=train_fraction,validation_fraction=validation_fraction,test_fraction=test_fraction,config=config,implementation_hash=implementation_hash,probability_predictor=probability_predictor).evaluate(rows,model_ids=model_ids,implementation_hash=implementation_hash,probability_predictor=probability_predictor)
    def build_frames(self, rows: Sequence[Mapping[str, Any]|TelemetryRow], model_id: str) -> tuple[dict[str, Any],...]: return self.adapter.frame(rows,model_id)
    def build_states(self, rows: Sequence[Mapping[str, Any]|TelemetryRow], model_id: str="M3") -> tuple[TiamatState,...]: return self.adapter.states(rows,model_id)
    def _evaluate_model(self, rows: tuple[TelemetryRow,...], model_id: str) -> CandidateTrial:
        axes=self.axes_for(model_id); supported=tuple(r for r in rows if r.supports(model_id,control_axes=self.control_axes)); coverage=len(supported)/len(rows) if rows else 0.0; transition_error=self._transition_error(rows,axes) if len(rows)>1 else None; spec=MODEL_REGISTRY.get(model_id); return CandidateTrial(model_id=model_id,role=spec.role if spec else "candidate",axes=axes,rows=len(rows),supported_rows=len(supported),coverage=coverage,transition_error=transition_error,complexity=len(axes),is_control=(model_id==self.control_model_id))
    def _transition_error(self, rows: tuple[TelemetryRow,...], axes: tuple[str,...]) -> float: return fmean([self._state_error(self.transition_fn(b.to_state(),a.to_mapping()),a.to_state(),axes) for b,a in zip(rows,rows[1:])]) if len(rows)>1 else 0.0
    def _state_error(self,predicted:TiamatState,observed:TiamatState,axes:tuple[str,...])->float:
        if not axes:return 0.0
        errors=[]
        for axis in axes:
            pv,ov=getattr(predicted,axis,None),getattr(observed,axis,None)
            if pv is None or ov is None: errors.append(1.0); continue
            if axis in {"B","D"}: errors.append(min(1.0,abs(float(pv)-float(ov))))
            elif axis in {"tau_D","tau_mode"}: of=float(ov); errors.append(min(1.0,abs(float(pv)-of)/max(1.0,abs(of))))
            elif axis in {"V","Phi"}: pf,of=float(pv),float(ov); errors.append(1.0 if not math.isfinite(pf) or not math.isfinite(of) else min(1.0,abs(pf-of)))
            else: errors.append(0.0 if pv==ov else 1.0)
        return fmean(errors) if errors else 0.0
    @staticmethod
    def _trial_order(trial: CandidateTrial)->tuple[float,float,float,int,str]: return (-trial.score,trial.transition_error if trial.transition_error is not None else 1.0,-trial.coverage,trial.complexity,trial.model_id)

IDENTIFICATION_RUNNER_VERSION="v1.1"
