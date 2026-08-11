from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence, Any

from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryAdapter, TelemetryRow


@dataclass(frozen=True, slots=True)
class ProjectionCollision:
    """Same DVQT projection, different observed next mode."""

    key: tuple[float, float, TiamatMode, float]
    indices: tuple[int, ...]
    next_modes: tuple[str, ...]
    full_rows: tuple[dict[str, Any], ...]


def find_projection_collisions(
    rows: Sequence[Mapping[str, Any] | TelemetryRow],
    *,
    adapter: TelemetryAdapter | None = None,
) -> tuple[ProjectionCollision, ...]:
    """Find empirical violations of the DVQT Markov claim.

    A collision exists when two rows have identical (D,V,q,tau) but their
    immediately observed next modes differ.  No threshold, distance metric,
    fitting, or future window is introduced: this is an exact falsification
    test of whether the proposed projection uniquely determines the next mode.
    """
    adapter = adapter or TelemetryAdapter()
    normalized = tuple(adapter.normalize(row) for row in rows)
    buckets: dict[tuple[float, float, TiamatMode, float], list[tuple[int, str, dict[str, Any]]]] = defaultdict(list)

    for index in range(len(normalized) - 1):
        current = normalized[index]
        nxt = normalized[index + 1]
        key = (current.D, current.V, current.mode, current.tau_mode)
        buckets[key].append((index, nxt.mode.value, current.to_mapping()))

    collisions: list[ProjectionCollision] = []
    for key, members in buckets.items():
        modes = tuple(sorted({mode for _, mode, _ in members}))
        if len(modes) > 1:
            collisions.append(
                ProjectionCollision(
                    key=key,
                    indices=tuple(index for index, _, _ in members),
                    next_modes=modes,
                    full_rows=tuple(row for _, _, row in members),
                )
            )
    return tuple(collisions)
