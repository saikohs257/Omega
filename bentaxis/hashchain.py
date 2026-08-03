from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterable

from bentaxis.identity import Identity, to_canonical_bytes
from runtime.events import Event


@dataclass(frozen=True, slots=True)
class HashChain:
    seed: str = ""
    links: tuple[str, ...] = field(default_factory=tuple)

    @property
    def head(self) -> str:
        return self.links[-1] if self.links else self.seed

    def append_event(self, event: Event) -> HashChain:
        event_id = Identity.calculate({"kind": event.kind, "payload": event.payload, "metadata": event.metadata}).digest
        next_head = hashlib.sha256(
            to_canonical_bytes({"prev": self.head, "event": event_id})
        ).hexdigest()
        return HashChain(seed=self.seed, links=self.links + (next_head,))

    def append_digest(self, digest: str) -> HashChain:
        next_head = hashlib.sha256(to_canonical_bytes({"prev": self.head, "digest": digest})).hexdigest()
        return HashChain(seed=self.seed, links=self.links + (next_head,))

    def extend(self, digests: Iterable[str]) -> HashChain:
        chain = self
        for digest in digests:
            chain = chain.append_digest(digest)
        return chain
