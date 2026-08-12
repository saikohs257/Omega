from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Mapping, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .telemetry import TelemetryRow

PROBABILITY_CONTRACT_VERSION = "probability-contract-v2"
METRIC_CONTRACT_VERSION = "metric-contract-v1.1"
LABEL_PROVENANCE_VERSION = "label-provenance-v2"
STATE_SPACE = ("Q", "P", "E", "C", "H", "R", "Rf")


@dataclass(frozen=True, slots=True)
class ProbabilityContract:
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
            raise ValueError(
                f"probability distribution sum {total:.17g} violates tolerance {self.sum_tolerance:.17g}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "state_space": list(self.state_space),
            "sum_tolerance": self.sum_tolerance,
            "violation_policy": self.violation_policy,
        }


class ProbabilityPredictor(Protocol):
    def __call__(self, row: "TelemetryRow") -> Mapping[str, float]: ...


@dataclass(frozen=True, slots=True)
class MetricContract:
    """Frozen definitions for NLL, multiclass Brier, and fixed-bin ECE."""

    probability_contract: ProbabilityContract
    nll_zero_clip: float = 1e-10
    brier_convention: str = "sum"
    ece_bins: int = 10
    ece_confidence: str = "max_probability"
    aggregation_level: str = "timestep"
    version: str = METRIC_CONTRACT_VERSION

    def __post_init__(self) -> None:
        clip = float(self.nll_zero_clip)
        bins = int(self.ece_bins)
        if not isfinite(clip) or not 0.0 < clip < 1.0:
            raise ValueError("nll_zero_clip must be finite and in (0, 1)")
        if self.brier_convention not in {"sum", "mean"}:
            raise ValueError("brier_convention must be sum or mean")
        if bins < 1:
            raise ValueError("ece_bins must be positive")
        if self.ece_confidence not in {"max_probability", "true_state_probability"}:
            raise ValueError("ece_confidence must be max_probability or true_state_probability")
        if self.aggregation_level not in {"timestep", "episode"}:
            raise ValueError("aggregation_level must be timestep or episode")
        object.__setattr__(self, "nll_zero_clip", clip)
        object.__setattr__(self, "ece_bins", bins)

    @property
    def state_space(self) -> tuple[str, ...]:
        return self.probability_contract.state_space

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "probability_contract": self.probability_contract.to_dict(),
            "nll": {
                "definition": "mean negative log probability assigned to the observed class",
                "zero_clip": self.nll_zero_clip,
            },
            "brier": {
                "definition": "mean sum of squared probability error across the full state space",
                "convention": self.brier_convention,
            },
            "ece": {
                "definition": "mean absolute confidence-accuracy gap over fixed-width confidence bins",
                "bins": self.ece_bins,
                "binning": "uniform_[0,1]",
                "confidence": self.ece_confidence,
                "accuracy": "top1_correct",
            },
            "aggregation": {"level": self.aggregation_level},
        }

    def nll(self, probabilities: Mapping[str, float], target: str) -> float:
        self.probability_contract.validate(probabilities)
        if target not in self.state_space:
            raise ValueError(f"unknown target state: {target}")
        return -log(max(float(probabilities[target]), self.nll_zero_clip))

    def brier(self, probabilities: Mapping[str, float], target: str) -> float:
        self.probability_contract.validate(probabilities)
        if target not in self.state_space:
            raise ValueError(f"unknown target state: {target}")
        value = sum(
            (float(probabilities[state]) - (1.0 if state == target else 0.0)) ** 2
            for state in self.state_space
        )
        if self.brier_convention == "mean":
            value /= len(self.state_space)
        return value

    def ece(self, rows: Sequence[tuple[Mapping[str, float], str]]) -> float:
        if not rows:
            raise ValueError("ECE requires at least one observation")
        buckets = [[] for _ in range(self.ece_bins)]
        for probabilities, target in rows:
            self.probability_contract.validate(probabilities)
            if target not in self.state_space:
                raise ValueError(f"unknown target state: {target}")
            if self.ece_confidence == "true_state_probability":
                confidence = float(probabilities[target])
            else:
                confidence = max(float(probabilities[s]) for s in self.state_space)
            prediction = max(self.state_space, key=lambda s: float(probabilities[s]))
            bucket_index = min(self.ece_bins - 1, int(confidence * self.ece_bins))
            buckets[bucket_index].append((confidence, prediction == target))
        total = len(rows)
        result = 0.0
        for bucket in buckets:
            if bucket:
                avg_conf = sum(c for c, _ in bucket) / len(bucket)
                avg_acc = sum(1.0 if ok else 0.0 for _, ok in bucket) / len(bucket)
                result += (len(bucket) / total) * abs(avg_conf - avg_acc)
        return result

    def score(self, rows: Sequence[tuple[Mapping[str, float], str]]) -> dict[str, float]:
        if not rows:
            raise ValueError("metric scoring requires at least one observation")
        return {
            "nll": sum(self.nll(p, t) for p, t in rows) / len(rows),
            "brier": sum(self.brier(p, t) for p, t in rows) / len(rows),
            "ece": self.ece(rows),
        }


@dataclass(frozen=True, slots=True)
class TargetProvenance:
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
            raise ValueError(
                f"label temporal exposure {self.label_temporal_offset} exceeds declared horizon {max_declared_future_steps}"
            )
        if self.label_episode_boundary_aware and not allow_episode_boundary_labels:
            raise ValueError("label uses eventual episode boundary without explicit allowance")

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "label_source": self.label_source,
            "label_version": self.label_version,
            "label_generation_method": self.label_generation_method,
            "label_confidence": self.label_confidence,
            "target_dependencies": list(self.target_dependencies),
            "label_corpus_hash": self.label_corpus_hash,
            "label_temporal_offset": self.label_temporal_offset,
            "label_episode_boundary_aware": self.label_episode_boundary_aware,
        }


LabelProvenance = TargetProvenance


def validate_probability_rows(rows: Sequence[Mapping[str, float]], contract: ProbabilityContract) -> None:
    for index, row in enumerate(rows):
        try:
            contract.validate(row)
        except ValueError as exc:
            raise ValueError(f"probability contract violation at row {index}: {exc}") from exc


def validate_probability_output(
    row: "TelemetryRow", predictor: ProbabilityPredictor, contract: ProbabilityContract
) -> Mapping[str, float]:
    output = predictor(row)
    if not isinstance(output, Mapping):
        raise TypeError("probability predictor must return a mapping")
    contract.validate(output)
    return output
