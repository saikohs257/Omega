from __future__ import annotations

from atlas.topology_contract import TopologyWitness
from tesseract.q4_contract import legal_edge


class TopologyCircuitBoundaryViolation(ValueError):
    """Raised when a circuit edge is not supported by a topology witness."""


def assert_witness_covers_edge(
    witness: TopologyWitness,
    from_node: str,
    to_node: str,
) -> None:
    """Require explicit topology evidence before admitting a Q4 circuit edge.

    This is an evidence boundary only. It does not infer missing relations,
    grant authority, or choose a transition.
    """
    if not legal_edge(from_node, to_node):
        raise TopologyCircuitBoundaryViolation(
            f"illegal Q4 circuit edge: {from_node!r}->{to_node!r}"
        )

    declared = {
        frozenset(nodes)
        for nodes, _label in witness.relations
        if len(nodes) == 2
    }
    if frozenset((from_node, to_node)) not in declared:
        raise TopologyCircuitBoundaryViolation(
            f"topology witness does not declare edge: {from_node!r}->{to_node!r}"
        )

    if not witness.verify():
        raise TopologyCircuitBoundaryViolation("topology witness is not internally closed")
