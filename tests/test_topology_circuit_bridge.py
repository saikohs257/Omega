from atlas.topology_contract import TopologyWitness
from tesseract.topology_circuit_bridge import (
    TopologyCircuitBoundaryViolation,
    assert_witness_covers_edge,
)


def test_topology_witness_admits_explicit_q4_edge() -> None:
    witness = TopologyWitness(
        atlas_dimension=4,
        coordinates=((0, 0, 0, 0),),
        relations=((("0101", "1101"), "q4"),),
        simplices=(),
    )
    assert_witness_covers_edge(witness, "0101", "1101")


def test_topology_witness_rejects_unproven_edge() -> None:
    witness = TopologyWitness(
        atlas_dimension=4,
        coordinates=((0, 0, 0, 0),),
        relations=((("0101", "1101"), "q4"),),
        simplices=(),
    )
    try:
        assert_witness_covers_edge(witness, "0101", "0111")
    except TopologyCircuitBoundaryViolation:
        return
    raise AssertionError("unproven circuit edge was admitted")


def test_topology_witness_rejects_multi_axis_jump() -> None:
    witness = TopologyWitness(
        atlas_dimension=4,
        coordinates=((0, 0, 0, 0),),
        relations=((("0101", "1101"), "q4"),),
        simplices=(),
    )
    try:
        assert_witness_covers_edge(witness, "0101", "1111")
    except TopologyCircuitBoundaryViolation:
        return
    raise AssertionError("multi-axis jump was admitted")
