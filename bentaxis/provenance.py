from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    source: str
    target: str
    relation: str


@dataclass(slots=True)
class ProvenanceGraph:
    nodes: set[str] = field(default_factory=set)
    edges: list[ProvenanceEdge] = field(default_factory=list)

    def add_node(self, identity: Identity) -> None:
        self.nodes.add(identity.digest)

    def link(self, source: Identity | str, target: Identity | str, relation: str) -> ProvenanceEdge:
        src = source.digest if isinstance(source, Identity) else source
        tgt = target.digest if isinstance(target, Identity) else target
        edge = ProvenanceEdge(source=src, target=tgt, relation=relation)
        self.nodes.add(src)
        self.nodes.add(tgt)
        self.edges.append(edge)
        return edge

    def related_to(self, digest: str) -> tuple[ProvenanceEdge, ...]:
        return tuple(edge for edge in self.edges if edge.source == digest or edge.target == digest)

    def extend_from_digests(self, digests: Iterable[str], relation: str = "derived_from") -> tuple[ProvenanceEdge, ...]:
        digests = tuple(digests)
        edges = []
        for left, right in zip(digests, digests[1:]):
            edges.append(self.link(left, right, relation))
        return tuple(edges)
