from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class ProvenanceManifest:
    """Content-addressed identity for an executable experiment boundary."""

    corpus_id: str
    information_set_id: str
    hypothesis_id: str
    implementation_id: str
    metric_contract_id: str
    output_contract_id: str
    manifest_id: str = ""

    def __post_init__(self) -> None:
        payload: Mapping[str, Any] = {
            "corpus_id": self.corpus_id,
            "information_set_id": self.information_set_id,
            "hypothesis_id": self.hypothesis_id,
            "implementation_id": self.implementation_id,
            "metric_contract_id": self.metric_contract_id,
            "output_contract_id": self.output_contract_id,
        }
        object.__setattr__(self, "manifest_id", Identity.calculate(payload).digest)
