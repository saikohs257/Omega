from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class Simplex:
    vertices: frozenset[str]
    metadata: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def create(cls, vertices: Iterable[str], metadata: dict[str, Any] | None = None) -> Simplex:
        return cls(vertices=frozenset(vertices), metadata=tuple(sorted((metadata or {}).items())))

    def dimension(self) -> int:
        return max(len(self.vertices) - 1, 0)

    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)


@dataclass(slots=True)
class SimplicialComplex:
    simplices: set[Simplex] = field(default_factory=set)

    def add_simplex(self, simplex: Simplex) -> None:
        self.simplices.add(simplex)
        vertices = tuple(simplex.vertices)
        for size in range(1, len(vertices)):
            self._add_faces(vertices, size)

    def _add_faces(self, vertices: tuple[str, ...], size: int) -> None:
        from itertools import combinations

        for combo in combinations(vertices, size):
            self.simplices.add(Simplex.create(combo))

    def add(self, vertices: Iterable[str], metadata: dict[str, Any] | None = None) -> Simplex:
        simplex = Simplex.create(vertices, metadata)
        self.add_simplex(simplex)
        return simplex

    def contains(self, vertices: Iterable[str]) -> bool:
        target = frozenset(vertices)
        return any(simplex.vertices == target for simplex in self.simplices)

    def count(self) -> int:
        return len(self.simplices)

    def maximal_simplices(self) -> tuple[Simplex, ...]:
        result = []
        for simplex in self.simplices:
            if not any(simplex.vertices < other.vertices for other in self.simplices):
                result.append(simplex)
        return tuple(result)
