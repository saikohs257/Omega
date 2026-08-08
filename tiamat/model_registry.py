"""Permanent TIAMAT identification model IDs.

IDs are never reused. A failed model remains failed and cannot be silently
renamed into a later experiment. This registry contains hypotheses only; it
confers no runtime authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelStatus(str, Enum):
    PROPOSED = "PROPOSED"
    FIT = "FIT"
    VALIDATED = "VALIDATED"
    OOS = "OOS"
    SURVIVED = "SURVIVED"
    FALSIFIED = "FALSIFIED"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    name: str
    state: tuple[str, ...]
    permanent_control: bool = False
    status: ModelStatus = ModelStatus.PROPOSED


MODEL_REGISTRY: tuple[ModelSpec, ...] = (
    ModelSpec("M0", "constant/no-state baseline", (), True),
    ModelSpec("M1", "burden-only", ("B",)),
    ModelSpec("M2", "burden-velocity", ("B", "V")),
    ModelSpec("M3", "core latent state", ("B", "V", "D")),
    ModelSpec("M4", "core + damage age", ("B", "V", "D", "tau_D")),
    ModelSpec("M5", "core + damage/mode age", ("B", "V", "D", "tau_D", "tau_M")),
    ModelSpec("M6", "core + memory + cross-axis evidence", ("B", "V", "D", "tau_D", "tau_M", "Phi")),
    ModelSpec("M7", "V6 control arm", ("F", "B", "R", "H", "O", "D", "Q", "phi"), True),
)

DYNAMICS_REGISTRY: tuple[str, ...] = ("D0", "D1", "D2", "D3", "D4")
RECOVERY_REGISTRY: tuple[str, ...] = ("R0", "R1", "R2", "R3", "R4")
DAMPING_REGISTRY: tuple[str, ...] = ("V0", "V1", "V2", "V3")
FORCING_REGISTRY: tuple[str, ...] = ("F0", "F1")


def get_model(model_id: str) -> ModelSpec:
    for model in MODEL_REGISTRY:
        if model.model_id == model_id:
            return model
    raise KeyError(f"unknown permanent model id: {model_id}")
