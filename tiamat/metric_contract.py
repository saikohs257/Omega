from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .telemetry import TelemetryRow

PROBABILITY_CONTRACT_VERSION = "probability-contract-v2"
LABEL_PROVENANCE_VERSION = "label-provenance-v2"
STATE_SPACE = ("Q", "P", "E", "C", "H", "R", "Rf")

@dataclass(frozen=True, slots=True)
class ProbabilityContract:
    """Precondition for probabilistic scoring; violations are rejected, never repaired."""
    state_space: tuple[str, ...]
    sum_tolerance: float = 1e-6
    violation_policy: str = "reject"
    version: str = PROBABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        states = tuple(str(s) for s in self.state_space)
        if not states or len(set(states)) != len(states):
            raise ValueError("state_space must contain unique states")
        if not isfinite(float(self.sum_tolerance)) or float(self.sum_tolerance) <= 0:
            raise ValueError("sum_tolerance must be finite and positive")
        if self.violation_policy != "reject":
            raise ValueError("probability violations must use reject policy")
        object.__setattr__(self, "state_space", states)
        object.__setattr__(self, "sum_tolerance", float(self.sum_tolerance))

    def validate(self, probabilities: Mapping[str, float]) -> None:
        missing = [s for s in self.state_space if s not in probabilities]
        extra = [str(k) for k in probabilities if str(k) not in self.state_space]
        if missing or extra:
            raise ValueError(f"probability state-space mismatch: missing={missing}, extra={extra}")
        values = [float(probabilities[s]) for s in self.state_space]
        if any(not isfinite(v) or v < 0.0 for v in values):
            raise ValueError("probability distribution contains non-finite or negative values")
        total = sum(values)
        if abs(total - 1.0) > self.sum_tolerance:
            raise ValueError(f"probability distribution sum {total:.17g} violates tolerance {self.sum_tolerance:.17g}")

    def to_dict(self) -> dict[str, object]:
        return {"version": self.version, "state_space": list(self.state_space), "sum_tolerance": self.sum_tolerance, "violation_policy": self.violation_policy}

class ProbabilityPredictor(Protocol):
    def __call__(self, row: "TelemetryRow") -> Mapping[str, float]: ...

@dataclass(frozen=True, slots=True)
class TargetProvenance:
    """Target provenance; target dependencies are never feature inputs."""
    label_source: str
    label_version: str
    label_generation_method: str
    label_confidence: float
    target_dependencies: tuple[str, ...]
    label_corpus_hash: str
    label_temporal_offset: int = 0
    label_episode_boundary_aware: bool = False
    version: str = LABEL_PROVENANCE_VERSION

    def __post_init__(self) -> None:
        if self.label_source not in {"observed", "proxy", "model_generated"}:
            raise ValueError("label_source must be observed, proxy, or model_generated")
        if not isfinite(float(self.label_confidence)) or not 0.0 <= float(self.label_confidence) <= 1.0:
            raise ValueError("label_confidence must be finite and in [0, 1]")
        if int(self.label_temporal_offset) < 0:
            raise ValueError("label_temporal_offset must be non-negative")
        if not self.label_corpus_hash:
            raise ValueError("label_corpus_hash is required")
        object.__setattr__(self, "target_dependencies", tuple(str(v) for v in self.target_dependencies))
        object.__setattr__(self, "label_confidence", float(self.label_confidence))
        object.__setattr__(self, "label_temporal_offset", int(self.label_temporal_offset))

    def validate(self, *, max_declared_future_steps: int, allow_episode_boundary_labels: bool = False) -> None:
        if self.label_temporal_offset > int(max_declared_future_steps):
            raise ValueError(f"label temporal exposure {self.label_temporal_offset} exceeds declared horizon {max_declared_future_steps}")
        if self.label_episode_boundary_aware and not allow_episode_boundary_labels:
            raise ValueError("label uses eventual episode boundary without explicit allowance")

    def to_dict(self) -> dict[str, object]:
        return {"version": self.version, "label_source": self.label_source, "label_version": self.label_version, "label_generation_method": self.label_generation_method, "label_confidence": self.label_confidence, "target_dependencies": list(self.target_dependencies), "label_corpus_hash": self.label_corpus_hash, "label_temporal_offset": self.label_temporal_offset, "label_episode_boundary_aware": self.label_episode_boundary_aware}

LabelProvenance = TargetProvenance

def validate_probability_rows(rows: Sequence[Mapping[str, float]], contract: ProbabilityContract) -> None:
    for index, row in enumerate(rows):
        try:
            contract.validate(row)
        except ValueError as exc:
            raise ValueError(f"probability contract violation at row {index}: {exc}") from exc

def validate_probability_output(row: "TelemetryRow", predictor: ProbabilityPredictor, contract: ProbabilityContract) -> Mapping[str, float]:
    output = predictor(row)
    if not isinstance(output, Mapping):
        raise TypeError("probability predictor must return a mapping")
    contract.validate(output)
    return output
