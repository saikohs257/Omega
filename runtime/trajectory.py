from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from runtime.events import Event


@dataclass(frozen=True, slots=True)
class Trajectory:
    """Append-only immutable event sequence."""

    events: tuple[Event, ...] = field(default_factory=tuple)

    def append(self, event: Event) -> Trajectory:
        return Trajectory(self.events + (event,))

    def extend(self, events: list[Event] | tuple[Event, ...] | Iterator[Event]) -> Trajectory:
        return Trajectory(self.events + tuple(events))

    def __iter__(self) -> Iterator[Event]:
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __bool__(self) -> bool:
        return bool(self.events)

    def last(self) -> Event | None:
        return self.events[-1] if self.events else None
