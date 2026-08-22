"""Q4 TESSERACT legal-topology contract.

This module deliberately implements only the recovered, source-backed topology
law: a 16-cell (4-bit) hypercube with 32 undirected legal edges and HOLD_SELF.
It does not grant runtime authority and does not choose a TIAMAT action.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product


Q4_DIMENSIONS = 4
Q4_NODE_COUNT = 16
Q4_EDGE_COUNT = 32
HOLD_SELF = "HOLD_SELF"


@dataclass(frozen=True, slots=True)
class Q4Edge:
    from_node: str
    to_node: str
    changed_axis: int

    @property
    def edge_id(self) -> str:
        return f"{self.from_node}->{self.to_node}"


def validate_node(node: str) -> str:
    if len(node) != Q4_DIMENSIONS or any(bit not in "01" for bit in node):
        raise ValueError(f"invalid Q4 node: {node!r}")
    return node


def encode(bits: tuple[int, int, int, int]) -> str:
    if len(bits) != Q4_DIMENSIONS or any(bit not in (0, 1) for bit in bits):
        raise ValueError(f"invalid Q4 bits: {bits!r}")
    return "".join(str(bit) for bit in bits)


def hamming_distance(left: str, right: str) -> int:
    validate_node(left)
    validate_node(right)
    return sum(a != b for a, b in zip(left, right))


def legal_edge(left: str, right: str) -> bool:
    return left != right and hamming_distance(left, right) == 1


def neighbors(node: str) -> tuple[str, ...]:
    validate_node(node)
    out = []
    for axis in range(Q4_DIMENSIONS):
        bits = list(node)
        bits[axis] = "1" if bits[axis] == "0" else "0"
        out.append("".join(bits))
    return tuple(out)


def edge(left: str, right: str) -> Q4Edge:
    if not legal_edge(left, right):
        raise ValueError(f"illegal Q4 edge: {left!r}->{right!r}")
    axis = next(i for i, (a, b) in enumerate(zip(left, right)) if a != b)
    return Q4Edge(left, right, axis)


def all_nodes() -> tuple[str, ...]:
    return tuple(encode(bits) for bits in product((0, 1), repeat=Q4_DIMENSIONS))


def undirected_edges() -> tuple[Q4Edge, ...]:
    edges: list[Q4Edge] = []
    for node in all_nodes():
        for neighbor in neighbors(node):
            if node < neighbor:
                edges.append(edge(node, neighbor))
    return tuple(edges)


if __name__ == "__main__":
    assert len(all_nodes()) == Q4_NODE_COUNT
    assert len(undirected_edges()) == Q4_EDGE_COUNT
