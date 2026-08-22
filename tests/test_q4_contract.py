from tesseract.q4_contract import (
    HOLD_SELF,
    Q4_EDGE_COUNT,
    Q4_NODE_COUNT,
    all_nodes,
    hamming_distance,
    legal_edge,
    neighbors,
    undirected_edges,
)


def test_q4_has_canonical_size() -> None:
    assert len(all_nodes()) == Q4_NODE_COUNT == 16
    assert len(undirected_edges()) == Q4_EDGE_COUNT == 32


def test_q4_legal_edge_is_exactly_one_axis() -> None:
    assert legal_edge("0101", "1101")
    assert hamming_distance("0101", "1101") == 1
    assert not legal_edge("0101", "1111")
    assert hamming_distance("0101", "1111") == 2


def test_q4_neighbors_are_single_axis_flips() -> None:
    assert set(neighbors("0101")) == {"1101", "0001", "0111", "0100"}


def test_hold_self_is_not_a_graph_edge() -> None:
    assert HOLD_SELF == "HOLD_SELF"
    assert not legal_edge("0101", "0101")
