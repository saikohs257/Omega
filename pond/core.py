from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
import hashlib
import json


class MutationOperation(str, Enum):
    SNIP = "SNIP"
    ALTER = "ALTER"
    HOLD = "HOLD"
    MERGE = "MERGE"


class LineageStatus(str, Enum):
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    ELIMINATED = "ELIMINATED"
    RESURRECTED = "RESURRECTED"


@dataclass(frozen=True, slots=True)
class MutationProposal:
    source_hypothesis: str
    source_failure: str
    diagnosis_id: str
    operation: MutationOperation
    target_component: str | None = None
    rationale: str = ""
    expected_effect: str = ""
    created_before_execution: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_hypothesis": self.source_hypothesis,
            "source_failure": self.source_failure,
            "diagnosis_id": self.diagnosis_id,
            "operation": self.operation.value,
            "target_component": self.target_component,
            "rationale": self.rationale,
            "expected_effect": self.expected_effect,
            "created_before_execution": self.created_before_execution,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PondEntry:
    hypothesis_id: str
    failure_id: str
    experiment_id: str
    hypothesis_definition_hash: str
    provenance_hash: str
    parent_id: str | None
    lineage_id: str
    failure_taxonomy: str
    diagnosis_ids: tuple[str, ...]
    mutation_budget: int
    resurrection_status: LineageStatus = LineageStatus.ACTIVE
    evidence_hashes: tuple[str, ...] = ()
    proposal: MutationProposal | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "failure_id": self.failure_id,
            "experiment_id": self.experiment_id,
            "hypothesis_definition_hash": self.hypothesis_definition_hash,
            "provenance_hash": self.provenance_hash,
            "parent_id": self.parent_id,
            "lineage_id": self.lineage_id,
            "failure_taxonomy": self.failure_taxonomy,
            "diagnosis_ids": list(self.diagnosis_ids),
            "mutation_budget": self.mutation_budget,
            "resurrection_status": self.resurrection_status.value,
            "evidence_hashes": list(self.evidence_hashes),
            "proposal": None if self.proposal is None else self.proposal.to_dict(),
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
