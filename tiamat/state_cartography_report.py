"""Baseline evaluation for trajectory-first state cartography.

The report intentionally uses only prediction trajectories. Ground-truth
mechanism names are retained only for post-hoc analysis and are never fed into
state encoding or distance calculations.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from .expanded_worlds import ExpandedWorld, build_expanded_worlds
from .state_cartography import StateFingerprint, distance, fingerprint


@dataclass(frozen=True, slots=True)
class WorldEmbedding:
    name: str
    trajectory: tuple[StateFingerprint, ...]


def _representative_stream(world: ExpandedWorld) -> tuple[float, ...]:
    """Represent a world without consulting its mechanism/truth labels."""
    streams = tuple(world.predictions.values())
    if not streams:
        return ()
    return tuple(sum(values) / len(values) for values in zip(*streams))


def embed(world: ExpandedWorld) -> WorldEmbedding:
    return WorldEmbedding(world.name, fingerprint(_representative_stream(world)))


def representative_distance(a: WorldEmbedding, b: WorldEmbedding) -> float:
    n = min(len(a.trajectory), len(b.trajectory))
    if n == 0:
        return 0.0
    return sum(distance(x, y) for x, y in zip(a.trajectory[:n], b.trajectory[:n])) / n


def pairwise_distances(embeddings: Iterable[WorldEmbedding]) -> dict[tuple[str, str], float]:
    rows = list(embeddings)
    return {
        (a.name, b.name): representative_distance(a, b)
        for a, b in combinations(rows, 2)
    }


def nearest_neighbors(embeddings: Iterable[WorldEmbedding], k: int = 3) -> dict[str, tuple[str, ...]]:
    rows = list(embeddings)
    out: dict[str, tuple[str, ...]] = {}
    for target in rows:
        ranked = sorted(
            ((representative_distance(target, other), other.name) for other in rows if other.name != target.name),
            key=lambda item: (item[0], item[1]),
        )
        out[target.name] = tuple(name for _, name in ranked[:k])
    return out


def main() -> None:
    worlds = build_expanded_worlds()
    embeddings = tuple(embed(world) for world in worlds)
    neighbors = nearest_neighbors(embeddings)
    print("TIAMAT STATE CARTOGRAPHY BASELINE")
    print(f"worlds={len(embeddings)}")
    print("NOTE=mechanism labels are not used by the encoder")
    for name, names in neighbors.items():
        print(f"WORLD {name} nearest={','.join(names)}")


if __name__ == "__main__":
    main()
