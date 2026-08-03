from hypergraph.engine import Hyperedge, Hypergraph


def test_hypergraph_add_and_query() -> None:
    graph = Hypergraph()
    edge = graph.add(["a", "b", "c"], "concept", {"weight": 3})
    assert graph.relation_count() == 1
    assert graph.contains(["a", "b", "c"], "concept")
    assert graph.contains(["c", "b", "a"], "concept")
    assert graph.neighbors("a") == (edge,)
    assert edge.metadata_dict() == {"weight": 3}


def test_hyperedge_is_hashable_and_stable() -> None:
    left = Hyperedge.create(["x", "y"], "rel", {"score": 1})
    right = Hyperedge.create(["y", "x"], "rel", {"score": 1})
    assert left == right
    assert len({left, right}) == 1
