from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from tiamat.telemetry import TelemetryRow


CANDIDATES = ("B", "D", "V", "mode", "tau_mode")


@dataclass(frozen=True, slots=True)
class StateCollision:
    projection: tuple[str, ...]
    key: tuple[Any, ...]
    next_modes: tuple[str, ...]
    rows: tuple[int, ...]

    @property
    def unresolved(self) -> bool:
        return len(self.next_modes) > 1


def value(row: TelemetryRow, field: str) -> Any:
    return getattr(row, field)


def find_collisions(rows: Sequence[TelemetryRow], projection: Sequence[str]) -> tuple[StateCollision, ...]:
    buckets: dict[tuple[Any, ...], list[tuple[int, TelemetryRow]]] = defaultdict(list)
    for i, (current, nxt) in enumerate(zip(rows, rows[1:])):
        buckets[tuple(value(current, field) for field in projection)].append((i, nxt))

    result = []
    for key, entries in buckets.items():
        modes = tuple(sorted({value(nxt, "mode").value for _, nxt in entries}))
        if len(modes) > 1:
            result.append(StateCollision(tuple(projection), key, modes, tuple(i for i, _ in entries)))
    return tuple(result)


def search_minimal_projections(
    worlds: Mapping[str, Sequence[TelemetryRow]],
) -> dict[str, Any]:
    """Enumerate small projections and report unresolved next-mode collisions.

    No fitting, optimization, or threshold selection is performed. A projection
    is better only when it removes exact present-state collisions with distinct
    observed next modes.
    """
    projections = (
        ("D", "V", "mode", "tau_mode"),
        ("B", "D", "V", "mode", "tau_mode"),
        ("B", "D", "V", "mode"),
        ("B", "D", "V", "tau_mode"),
        ("B", "D", "V"),
    )
    report: dict[str, Any] = {}
    for projection in projections:
        per_world = {}
        total = 0
        for name, rows in worlds.items():
            collisions = find_collisions(rows, projection)
            per_world[name] = len(collisions)
            total += len(collisions)
        report["+".join(projection)] = {"total_unresolved_collisions": total, "per_world": per_world}
    return report
