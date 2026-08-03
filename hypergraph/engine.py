from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, FrozenSet, Iterable


@dataclass(frozen=True, slots=True)
class Hyperedge:
    nodes: frozenset[str]
    label: str
    metadata: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def create(cls, nodes: Iterable[str], label: str, metadata: dict[str, Any] | None = None) -> Hyperedge:
        metadata_items = tuple(sorted((metadata or {}).items()))
        return cls(nodes=frozenset(nodes), label=label, metadata=metadata_items)

    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)


@dataclass(slots=True)
class Hypergraph:
    edges: set[Hyperedge] = field(default_factory=set)

    def add_edge(self, edge: Hyperedge) -> None:
        self.edges.add(edge)

    def add(self, nodes: Iterable[str], label: str, metadata: dict[str, Any] | None = None) -> Hyperedge:
        edge = Hyperedge.create(nodes, label, metadata)
        self.add_edge(edge)
        return edge

    def neighbors(self, node: str) -> tuple[Hyperedge, ...]:
        return tuple(edge for edge in self.edges if node in edge.nodes)

    def relation_count(self) -> int:
        return len(self.edges)

    def contains(self, nodes: Iterable[str], label: str) -> bool:
        target = frozenset(nodes)
        return any(edge.nodes == target and edge.label == label for edge in self.edges)
