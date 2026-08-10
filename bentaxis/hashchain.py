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

    @staticmethod
    def _event_digest(event: Event) -> str:
        return Identity.calculate(
            {"kind": event.kind, "payload": event.payload, "metadata": event.metadata}
        ).digest

    @staticmethod
    def _next_head(previous: str, digest: str) -> str:
        return hashlib.sha256(
            to_canonical_bytes({"prev": previous, "event": digest})
        ).hexdigest()

    def append_event(self, event: Event) -> HashChain:
        next_head = self._next_head(self.head, self._event_digest(event))
        return HashChain(seed=self.seed, links=self.links + (next_head,))

    def append_digest(self, digest: str) -> HashChain:
        next_head = hashlib.sha256(to_canonical_bytes({"prev": self.head, "digest": digest})).hexdigest()
        return HashChain(seed=self.seed, links=self.links + (next_head,))

    def extend(self, digests: Iterable[str]) -> HashChain:
        chain = self
        for digest in digests:
            chain = chain.append_digest(digest)
        return chain

    def verify_events(self, events: Iterable[Event]) -> bool:
        """Return whether the chain exactly matches the supplied event sequence."""
        expected = HashChain(seed=self.seed)
        event_tuple = tuple(events)
        if len(self.links) != len(event_tuple):
            return False
        for event in event_tuple:
            expected = expected.append_event(event)
        return expected.links == self.links
