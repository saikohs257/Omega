from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
import hashlib
import json


class FailureTaxonomy(str, Enum):
    STRUCTURAL = "structural"
    DYNAMIC = "dynamic"
    TEMPORAL = "temporal"
    STATISTICAL = "statistical"
    DATA = "data"
    EXPERIMENTAL = "experimental"
    IMPLEMENTATION = "implementation"
    UNKNOWN = "unknown"


class CertaintyLevel(str, Enum):
    UNKNOWN = "UNKNOWN"
    CORRELATED = "CORRELATED"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"


@dataclass(frozen=True, slots=True)
class Diagnosis:
    taxonomy: FailureTaxonomy = FailureTaxonomy.UNKNOWN
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    summary: str = ""
    rationale: str = ""
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "taxonomy": self.taxonomy.value,
            "certainty": self.certainty.value,
            "summary": self.summary,
            "rationale": self.rationale,
            "version": self.version,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FailureRecord:
    failure_id: str
    experiment_id: str
    hypothesis_id: str
    corpus_hash: str
    information_set_hash: str
    metric_contract_hash: str
    implementation_hash: str
    outcome: str
    metrics: Mapping[str, Any]
    residuals: Mapping[str, Any]
    stratum_results: Mapping[str, Any]
    reliability_results: Mapping[str, Any]
    diagnosis: Diagnosis
    created_at: str

    def content_hash(self) -> str:
        payload = self.to_dict()
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "experiment_id": self.experiment_id,
            "hypothesis_id": self.hypothesis_id,
            "corpus_hash": self.corpus_hash,
            "information_set_hash": self.information_set_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "implementation_hash": self.implementation_hash,
            "outcome": self.outcome,
            "metrics": dict(self.metrics),
            "residuals": dict(self.residuals),
            "stratum_results": dict(self.stratum_results),
            "reliability_results": dict(self.reliability_results),
            "diagnosis": self.diagnosis.to_dict(),
            "created_at": self.created_at,
        }
