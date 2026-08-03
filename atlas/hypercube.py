from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.interface import Atlas, AtlasNeighborhood


@dataclass(frozen=True, slots=True)
class HypercubeAtlas:
    dimensions: int

    def project(self, state: Any) -> tuple[int, ...]:
        if isinstance(state, dict):
            values = tuple(int(bool(state.get(f"axis_{i}", 0))) for i in range(self.dimensions))
        elif isinstance(state, (list, tuple)):
            values = tuple(int(x) for x in state[: self.dimensions])
        else:
            values = tuple(0 for _ in range(self.dimensions))
        if len(values) != self.dimensions:
            values = values + tuple(0 for _ in range(self.dimensions - len(values)))
        return values

    def distance(self, left: tuple[int, ...], right: tuple[int, ...]) -> int:
        if len(left) != len(right):
            raise ValueError("Hypercube distance requires coordinates with matching dimensionality")
        return sum(abs(a - b) for a, b in zip(left, right))

    def get_neighbors(self, coordinate: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        if len(coordinate) != self.dimensions:
            raise ValueError("Coordinate dimensionality does not match atlas dimensions")
        neighbors = []
        for idx in range(self.dimensions):
            flipped = list(coordinate)
            flipped[idx] = 1 - int(bool(flipped[idx]))
            neighbors.append(tuple(flipped))
        return tuple(neighbors)

    def local_chart(self, coordinate: tuple[int, ...]) -> AtlasNeighborhood:
        return AtlasNeighborhood(origin=coordinate, neighbors=self.get_neighbors(coordinate))
