from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow


@dataclass(frozen=True, slots=True)
class ProjectionCollision:
    key: tuple[Any, ...]
    observations: int
    distinct_next_modes: tuple[str, ...]
    distinct_B: tuple[float, ...]
    indices: tuple[int, ...]

    @property
    def is_non_deterministic(self) -> bool:
        return len(self.distinct_next_modes) > 1


def projection_key(row: TelemetryRow) -> tuple[Any, ...]:
    """The exact DVQT projection under test."""
    return (row.D, row.V, row.mode, row.tau_mode)


def find_projection_collisions(rows: Sequence[TelemetryRow]) -> tuple[ProjectionCollision, ...]:
    """Find identical DVQT states followed by different observed next modes."""
    buckets: dict[tuple[Any, ...], list[tuple[int, TelemetryRow, TelemetryRow]]] = defaultdict(list)
    for index, (current, nxt) in enumerate(zip(rows, rows[1:])):
        buckets[projection_key(current)].append((index, current, nxt))

    collisions: list[ProjectionCollision] = []
    for key, entries in buckets.items():
        modes = tuple(sorted({entry[2].mode.value for entry in entries}))
        if len(modes) < 2:
            continue
        b_values = tuple(sorted({entry[1].B for entry in entries}))
        collisions.append(
            ProjectionCollision(
                key=key,
                observations=len(entries),
                distinct_next_modes=modes,
                distinct_B=b_values,
                indices=tuple(entry[0] for entry in entries),
            )
        )
    return tuple(collisions)


def analyze_worlds(
    worlds: Mapping[str, Sequence[TelemetryRow]],
) -> dict[str, Any]:
    """Aggregate exact DVQT collisions without fitting or threshold tuning."""
    per_world: dict[str, Any] = {}
    all_collisions: list[tuple[str, ProjectionCollision]] = []
    for name, rows in worlds.items():
        collisions = find_projection_collisions(rows)
        per_world[name] = {
            "rows": len(rows),
            "collisions": len(collisions),
            "collisions_explained_by_B": sum(
                1 for c in collisions if len(c.distinct_B) > 1
            ),
            "collisions_not_explained_by_B": sum(
                1 for c in collisions if len(c.distinct_B) <= 1
            ),
            "details": [
                {
                    "key": tuple(str(x) for x in c.key),
                    "observations": c.observations,
                    "distinct_next_modes": c.distinct_next_modes,
                    "distinct_B": c.distinct_B,
                    "indices": c.indices,
                }
                for c in collisions
            ],
        }
        all_collisions.extend((name, c) for c in collisions)

    return {
        "worlds": len(worlds),
        "worlds_with_collisions": sum(bool(find_projection_collisions(rows)) for rows in worlds.values()),
        "total_collisions": len(all_collisions),
        "collisions_with_B_variation": sum(len(c.distinct_B) > 1 for _, c in all_collisions),
        "collisions_without_B_variation": sum(len(c.distinct_B) <= 1 for _, c in all_collisions),
        "per_world": per_world,
    }
