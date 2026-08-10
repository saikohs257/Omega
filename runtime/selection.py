from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class SelectionThresholds:
    """Frozen numeric and semantic contract for candidate selection."""

    brier_skill_min: float = 0.05
    auc_min: float = 0.5
    ece_max: float = 0.10
    version: str = "selection-thresholds-v1"

    def __post_init__(self) -> None:
        for name in ("brier_skill_min", "auc_min", "ece_max"):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.auc_min <= 1.0:
            raise ValueError("auc_min must be in [0, 1]")
        if not 0.0 <= self.ece_max <= 1.0:
            raise ValueError("ece_max must be in [0, 1]")
        if not self.version:
            raise ValueError("selection threshold version must be non-empty")

    def canonical_payload(self) -> Mapping[str, Any]:
        return {
            "version": self.version,
            "brier_skill_min": self.brier_skill_min,
            "auc_min": self.auc_min,
            "ece_max": self.ece_max,
        }

    @property
    def selection_thresholds_hash(self) -> str:
        return Identity.calculate(self.canonical_payload()).digest
