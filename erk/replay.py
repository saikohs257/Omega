from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .core import Action, AuthorityGrant, EpistemicState, EvidenceRecord, state_hash
from .grants import ConsumedGrantRegistry, evidence_digest


@dataclass(frozen=True, slots=True)
class ReplayRecord:
    sequence: int
    state_hash: str
    evidence_hash: str
    policy_hash: str
    branch_id: str
    action: str
    grant_id: str | None
    registry_hash: str
    previous_hash: str
    transition_hash: str

    def canonical(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()


def make_replay_record(sequence: int, state: EpistemicState, evidence: tuple[EvidenceRecord, ...], action: Action, registry: ConsumedGrantRegistry, previous_hash: str = "", grant: AuthorityGrant | None = None) -> ReplayRecord:
    record = ReplayRecord(sequence, state_hash(state), evidence_digest(evidence), state.policy_version, state.branch_id, action.value, grant.grant_id if grant else None, registry.digest(), previous_hash, "")
    digest = sha256(record.canonical()).hexdigest()
    return ReplayRecord(sequence, record.state_hash, record.evidence_hash, record.policy_hash, record.branch_id, record.action, record.grant_id, record.registry_hash, record.previous_hash, digest)


def verify_replay_chain(records: tuple[ReplayRecord, ...]) -> bool:
    previous = ""
    for index, record in enumerate(records):
        if record.sequence != index or record.previous_hash != previous: return False
        unsigned = ReplayRecord(record.sequence, record.state_hash, record.evidence_hash, record.policy_hash, record.branch_id, record.action, record.grant_id, record.registry_hash, record.previous_hash, "")
        if sha256(unsigned.canonical()).hexdigest() != record.transition_hash: return False
        previous = record.transition_hash
    return True
