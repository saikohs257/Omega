from __future__ import annotations

from dataclasses import dataclass
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
        return json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode()


def make_replay_record(
    sequence: int,
    state: EpistemicState,
    evidence: tuple[EvidenceRecord, ...],
    action: Action,
    registry: ConsumedGrantRegistry,
    previous_hash: str = "",
    grant: AuthorityGrant | None = None,
) -> ReplayRecord:
    record = ReplayRecord(
        sequence=sequence,
        state_hash=state_hash(state),
        evidence_hash=evidence_digest(evidence),
        policy_hash=state.policy_version,
        branch_id=state.branch_id,
        action=action.value,
        grant_id=grant.grant_id if grant else None,
        registry_hash=registry.digest(),
        previous_hash=previous_hash,
        transition_hash="",
    )
    digest = sha256(record.canonical()).hexdigest()
    return ReplayRecord(**{**record.__dict__, "transition_hash": digest})


def verify_replay_chain(records: tuple[ReplayRecord, ...]) -> bool:
    previous = ""
    for index, record in enumerate(records):
        if record.sequence != index: return False
        if record.previous_hash != previous: return False
        unsigned = ReplayRecord(record.sequence, record.state_hash, record.evidence_hash, record.policy_hash, record.branch_id, record.action, record.grant_id, record.registry_hash, record.previous_hash, "")
        if sha256(unsigned.canonical()).hexdigest() != record.transition_hash: return False
        previous = record.transition_hash
    return True
