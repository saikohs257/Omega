from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from .core import Authority, AuthorityGrant, EpistemicState, EvidenceRecord, state_hash


@dataclass(frozen=True, slots=True)
class ConsumedGrantRegistry:
    nonces: frozenset[str] = frozenset()

    def consume(self, grant: AuthorityGrant) -> "ConsumedGrantRegistry":
        if grant.nonce in self.nonces:
            raise ValueError("authority grant already consumed")
        return ConsumedGrantRegistry(self.nonces | {grant.nonce})

    def contains(self, nonce: str) -> bool:
        return nonce in self.nonces

    def digest(self) -> str:
        payload = json.dumps(sorted(self.nonces), separators=(",", ":")).encode()
        return sha256(payload).hexdigest()


def evidence_digest(evidence: Iterable[EvidenceRecord]) -> str:
    return sha256(b"".join(e._canonical_content() for e in evidence)).hexdigest()


def bind_grant_to_registry(grant: AuthorityGrant, registry: ConsumedGrantRegistry) -> AuthorityGrant:
    if registry.contains(grant.nonce):
        raise ValueError("authority grant nonce already consumed")
    return grant


def verify_and_consume_grant(
    grant: AuthorityGrant,
    state: EpistemicState,
    evidence: tuple[EvidenceRecord, ...],
    registry: ConsumedGrantRegistry,
    kernel_secret: bytes,
) -> tuple[AuthorityGrant, ConsumedGrantRegistry]:
    from .core import verify_authority_grant

    bind_grant_to_registry(grant, registry)
    if not verify_authority_grant(grant, state, evidence, kernel_secret, registry.nonces):
        raise ValueError("invalid authority grant")
    return grant, registry.consume(grant)
