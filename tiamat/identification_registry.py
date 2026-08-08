"""Permanent TIAMAT identification registry and experiment fingerprints."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from types import MappingProxyType
from .experiment_manifest import canonical_hash


@dataclass(frozen=True, slots=True)
class ProbabilityAdapterDeclaration:
    adapter_type: str = "native"
    adapter_version: str = "v1"
    adapter_hash: str = ""
    calibration_corpus_hash: str | None = None
    known_limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.adapter_type not in {"platt", "isotonic", "degenerate", "native"}:
            raise ValueError("unsupported probability adapter type")
        if self.adapter_type in {"platt", "isotonic"} and not self.calibration_corpus_hash:
            raise ValueError("calibration_corpus_hash is required for fitted probability adapters")
        if self.adapter_type != "native" and not self.adapter_hash:
            raise ValueError("adapter_hash is required for non-native probability adapters")
        object.__setattr__(self, "known_limitations", tuple(str(v) for v in self.known_limitations))


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    state: tuple[str, ...] | str
    role: str
    version: str = "v1"
    probability_adapter: ProbabilityAdapterDeclaration = ProbabilityAdapterDeclaration()


MODEL_REGISTRY = MappingProxyType({
    "M0": ModelSpec("M0", ("B",), "burden baseline"),
    "M1": ModelSpec("M1", ("B", "V"), "first dynamic candidate"),
    "M2": ModelSpec("M2", ("B", "D"), "damage candidate"),
    "M3": ModelSpec("M3", ("B", "V", "D"), "primary reduced-state candidate"),
    "M4": ModelSpec("M4", ("B", "V", "D", "tau_D"), "damage-memory candidate"),
    "M5": ModelSpec("M5", ("B", "V", "D", "tau_D", "tau_M"), "temporal-memory candidate"),
    "M6": ModelSpec("M6", ("B", "V", "D", "tau_D", "tau_M", "Phi"), "cross-axis candidate"),
    "M7": ModelSpec(
        "M7", "V6_control", "permanent V6 control",
        probability_adapter=ProbabilityAdapterDeclaration(
            adapter_type="native",
            known_limitations=("historical control must expose a native probability distribution; otherwise register as incomparable",),
        ),
    ),
})

DYNAMICS_REGISTRY = MappingProxyType({
    "D0": "no persistent damage", "D1": "linear damage", "D2": "yield damage",
    "D3": "yield plus rate", "D4": "yield plus creep",
})
RECOVERY_REGISTRY = MappingProxyType({
    "R0": "constant recovery", "R1": "exponential damage-dependent recovery",
    "R2": "power-law damage-dependent recovery", "R3": "damage plus tau_D recovery",
    "R4": "damage plus tau_D plus mode recovery",
})
DAMPING_REGISTRY = MappingProxyType({
    "V0": "linear damping", "V1": "damage-increasing damping",
    "V2": "damage-decreasing damping", "V3": "nonlinear damping",
})
FORCING_REGISTRY = MappingProxyType({"F0": "instantaneous forcing", "F1": "filtered forcing"})

DAMAGE_THRESHOLD_CANDIDATE = 0.343
EXCITATION_THRESHOLD_CANDIDATE = 0.599
HAZARD_THRESHOLD_CANDIDATE = 0.794
REFRACTORY_RELEASE_CANDIDATE = 0.95
CANONICAL_THRESHOLDS = MappingProxyType({
    "hazard_low": 0.343, "hazard_medium": 0.599, "hazard_high": 0.794,
    "refractory_dormancy": 0.95,
})
RETIRED_CONTROLS = frozenset({"fixed_6h_choke_timer"})


def model(model_id: str) -> ModelSpec:
    try:
        return MODEL_REGISTRY[model_id]
    except KeyError as exc:
        raise KeyError(f"unknown TIAMAT model id: {model_id}") from exc


def registry_fingerprint() -> str:
    payload = {k: asdict(v) for k, v in sorted(MODEL_REGISTRY.items())}
    return canonical_hash(payload)
