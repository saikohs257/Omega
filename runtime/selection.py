from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class SelectionThresholds:
    """Frozen numeric and semantic contract for candidate selection."""

    brier_skill_min: float = 0.05
    auc_min: float = 0.0
    ece_max: float = 0.10
    version: str = "selection-thresholds-v1"

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
