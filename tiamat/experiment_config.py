from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence

TOURNAMENT_CONFIG_VERSION = "tournament-config-v1"
TEMPORAL_CAUSAL_GATE_VERSION = "causal-gate-v1"

DEFAULT_METRIC_WEIGHTS: dict[str, float] = {
    "nll": 1.0,
    "brier": 1.0,
    "ece": 1.0,
    "transition_error": 1.0,
    "complexity": 1.0,
    "stability": 1.0,
}

DEFAULT_FORBIDDEN_FUTURE_KEYS: tuple[str, ...] = (
    "episode_end",
    "future_duration",
    "future_guard_reason",
    "future_peak",
    "future_target",
    "label_next",
    "next_guard_reason",
    "next_peak",
    "next_target",
    "target_t_plus_1",
)

DEFAULT_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "future_",
    "next_",
    "label_next_",
    "target_next_",
    "y_next_",
)

DEFAULT_FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    "_future",
    "_next",
    "_t+1",
)


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=repr)
    return value


@dataclass(frozen=True, slots=True)
class TournamentConfig:
    """Frozen configuration for the TIAMAT identification tournament."""

    metric_weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_METRIC_WEIGHTS))
    split_boundaries: tuple[float, float, float] = (0.6, 0.2, 0.2)
    max_markov_lag: int = 10
    complexity_definition: str = "axis_count"
    stability_definition: str = "innovation_autocorrelation_plus_parameter_stability"
    random_seed: int = 0
    telemetry_schema_version: str = "tiamat.telemetry.v1"
    config_version: str = TOURNAMENT_CONFIG_VERSION

    def __post_init__(self) -> None:
        normalized_weights: dict[str, float] = {}
        for name, value in self.metric_weights.items():
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError(f"metric weight {name} must be finite and non-negative")
            normalized_weights[str(name)] = numeric
        object.__setattr__(self, "metric_weights", dict(sorted(normalized_weights.items())))

        fractions = tuple(float(value) for value in self.split_boundaries)
        if len(fractions) != 3:
            raise ValueError("split_boundaries must contain exactly three values")
        if any(not math.isfinite(value) or value < 0.0 for value in fractions):
            raise ValueError("split_boundaries must be finite and non-negative")
        if not math.isclose(sum(fractions), 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("split_boundaries must sum to 1.0")
        object.__setattr__(self, "split_boundaries", fractions)

        lag = int(self.max_markov_lag)
        if lag < 1:
            raise ValueError("max_markov_lag must be at least 1")
        object.__setattr__(self, "max_markov_lag", lag)

        if not isinstance(self.complexity_definition, str) or not self.complexity_definition:
            raise ValueError("complexity_definition must be a non-empty string")
        if not isinstance(self.stability_definition, str) or not self.stability_definition:
            raise ValueError("stability_definition must be a non-empty string")
        if not isinstance(self.telemetry_schema_version, str) or not self.telemetry_schema_version:
            raise ValueError("telemetry_schema_version must be a non-empty string")
        if not isinstance(self.config_version, str) or not self.config_version:
            raise ValueError("config_version must be a non-empty string")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "config_version": self.config_version,
            "metric_weights": dict(self.metric_weights),
            "split_boundaries": list(self.split_boundaries),
            "max_markov_lag": self.max_markov_lag,
            "complexity_definition": self.complexity_definition,
            "stability_definition": self.stability_definition,
            "random_seed": self.random_seed,
            "telemetry_schema_version": self.telemetry_schema_version,
        }

    def config_hash(self) -> str:
        payload = _canonical(self.canonical_payload())
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload() | {"config_hash": self.config_hash()}


@dataclass(frozen=True, slots=True)
class TemporalCausalGate:
    """Strict temporal boundary for held-out identification."""

    max_lookback: int = 10
    forbidden_keys: tuple[str, ...] = DEFAULT_FORBIDDEN_FUTURE_KEYS
    forbidden_prefixes: tuple[str, ...] = DEFAULT_FORBIDDEN_PREFIXES
    forbidden_suffixes: tuple[str, ...] = DEFAULT_FORBIDDEN_SUFFIXES
    gate_version: str = TEMPORAL_CAUSAL_GATE_VERSION

    def __post_init__(self) -> None:
        lag = int(self.max_lookback)
        if lag < 1:
            raise ValueError("max_lookback must be at least 1")
        object.__setattr__(self, "max_lookback", lag)
        object.__setattr__(self, "forbidden_keys", tuple(str(item) for item in self.forbidden_keys))
        object.__setattr__(self, "forbidden_prefixes", tuple(str(item) for item in self.forbidden_prefixes))
        object.__setattr__(self, "forbidden_suffixes", tuple(str(item) for item in self.forbidden_suffixes))
        if not isinstance(self.gate_version, str) or not self.gate_version:
            raise ValueError("gate_version must be a non-empty string")

    def _mapping(self, row: Mapping[str, Any] | Any) -> Mapping[str, Any]:
        if hasattr(row, "to_mapping"):
            mapping = getattr(row, "to_mapping")()
            return mapping if isinstance(mapping, Mapping) else dict(mapping)
        return row if isinstance(row, Mapping) else dict(row)

    def validate_row(self, row: Mapping[str, Any] | Any) -> None:
        mapping = self._mapping(row)
        contaminated: list[str] = []
        for key in mapping.keys():
            name = str(key)
            if (
                name in self.forbidden_keys
                or any(name.startswith(prefix) for prefix in self.forbidden_prefixes)
                or any(name.endswith(suffix) for suffix in self.forbidden_suffixes)
                or "t+1" in name
            ):
                contaminated.append(name)
        if contaminated:
            raise ValueError(f"temporal contamination detected: {', '.join(sorted(set(contaminated)))}")

    def validate_rows(self, rows: Sequence[Mapping[str, Any] | Any]) -> None:
        for row in rows:
            self.validate_row(row)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_version": self.gate_version,
            "max_lookback": self.max_lookback,
            "forbidden_keys": list(self.forbidden_keys),
            "forbidden_prefixes": list(self.forbidden_prefixes),
            "forbidden_suffixes": list(self.forbidden_suffixes),
        }
