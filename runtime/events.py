from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable atomic runtime record."""

    kind: str
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        kind: str,
        payload: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Event:
        payload_items = tuple(sorted((payload or {}).items()))
        metadata_items = tuple(sorted((metadata or {}).items()))
        return cls(kind=kind, payload=payload_items, metadata=metadata_items)

    def payload_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)

    def with_metadata(self, **updates: Any) -> Event:
        merged = self.metadata_dict()
        merged.update(updates)
        return Event.create(self.kind, self.payload_dict(), merged)
