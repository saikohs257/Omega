from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity
from runtime.contracts import OutputContract
from runtime.information_set import InformationSet


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    hypothesis_id: str
    information_set: InformationSet
    metric_contract: str
    output_contract: OutputContract
    implementation_id: str
    experiment_id: str = ""

    def __post_init__(self) -> None:
        payload: Mapping[str, Any] = {
            "hypothesis_id": self.hypothesis_id,
            "information_set_id": self.information_set.information_set_id,
            "metric_contract": self.metric_contract,
            "output_kind": self.output_contract.kind.value,
            "output_name": self.output_contract.name,
            "output_version": self.output_contract.version,
            "implementation_id": self.implementation_id,
        }
        object.__setattr__(self, "experiment_id", Identity.calculate(payload).digest)

    def require_probability(self) -> None:
        self.output_contract.require_probability()
