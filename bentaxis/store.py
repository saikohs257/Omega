from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from bentaxis.hashchain import HashChain
from bentaxis.identity import Identity
from runtime.events import Event


@dataclass(frozen=True, slots=True)
class StoredEvent:
    identity: Identity
    event: Event


@dataclass(slots=True)
class BentAxisStore:
    _events: list[StoredEvent] = field(default_factory=list)
    _chain: HashChain = field(default_factory=HashChain)

    @property
    def chain(self) -> HashChain:
        return self._chain

    @property
    def events(self) -> tuple[StoredEvent, ...]:
        return tuple(self._events)

    def append(self, event: Event) -> StoredEvent:
        if not isinstance(event, Event):
            raise TypeError("event must be an Event")
        record = StoredEvent(
            identity=Identity.calculate({"kind": event.kind, "payload": event.payload, "metadata": event.metadata}),
            event=event,
        )
        self._events.append(record)
        self._chain = self._chain.append_event(event)
        return record

    def append_many(self, events: Iterable[Event]) -> tuple[StoredEvent, ...]:
        records = []
        for event in events:
            records.append(self.append(event))
        return tuple(records)

    def get(self, digest: str) -> StoredEvent | None:
        for record in self._events:
            if record.identity.digest == digest:
                return record
        return None

    def verify_integrity(self) -> bool:
        """Verify identities, ordering, and the complete append-only hash chain."""
        events = tuple(record.event for record in self._events)
        if any(
            record.identity.digest
            != Identity.calculate({"kind": record.event.kind, "payload": record.event.payload, "metadata": record.event.metadata}).digest
            for record in self._events
        ):
            return False
        return self._chain.verify_events(events)

    def snapshot(self) -> dict[str, Any]:
        return {
            "count": len(self._events),
            "chain_head": self._chain.head,
            "digests": [record.identity.digest for record in self._events],
        }
