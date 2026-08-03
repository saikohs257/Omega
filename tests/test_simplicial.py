from simplicial.complex import Simplex, SimplicialComplex


def test_simplicial_adds_faces_and_maximals() -> None:
    complex_ = SimplicialComplex()
    simplex = complex_.add(["a", "b", "c"], {"kind": "concept"})
    assert simplex.dimension() == 2
    assert complex_.contains(["a", "b", "c"])
    assert complex_.contains(["a", "b"])
    assert complex_.contains(["a"])
    assert complex_.count() >= 4
    assert any(item.vertices == frozenset({"a", "b", "c"}) for item in complex_.maximal_simplices())


def test_simplex_metadata_is_deterministic() -> None:
    left = Simplex.create(["x", "y"], {"score": 1})
    right = Simplex.create(["y", "x"], {"score": 1})
    assert left == right
    assert left.metadata_dict() == {"score": 1}
