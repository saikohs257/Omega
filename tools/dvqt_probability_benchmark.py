from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from tiamat.telemetry import TelemetryRow


PROJECTIONS = (
    ("DVQT", ("D", "V", "mode", "tau_mode")),
    ("DVQT+B", ("D", "V", "mode", "tau_mode", "B")),
    ("DVQ+B", ("D", "V", "mode", "B")),
    ("DV+B", ("D", "V", "B")),
)


def brier(rows: Sequence[TelemetryRow], fields: Sequence[str]) -> float:
    """Leave-one-out empirical transition probability Brier score."""
    buckets: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for current, nxt in zip(rows, rows[1:]):
        key = tuple(getattr(current, f) for f in fields)
        buckets[key].append(1 if nxt.mode.value == "EXCITATION" else 0)
    loss = []
    for values in buckets.values():
        n = len(values)
        if n < 2:
            continue
        for y in values:
            p = (sum(values) - y) / (n - 1)
            loss.append((p - y) ** 2)
    return sum(loss) / len(loss) if loss else float("nan")


def benchmark(worlds: Mapping[str, Sequence[TelemetryRow]]) -> dict[str, Any]:
    out = {}
    for name, fields in PROJECTIONS:
        scores = {world: brier(rows, fields) for world, rows in worlds.items()}
        finite = [x for x in scores.values() if x == x]
        out[name] = {
            "dimensions": len(fields),
            "mean_brier": sum(finite) / len(finite) if finite else float("nan"),
            "world_brier": scores,
        }
    return out
