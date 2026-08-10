from atlas.hypercube import HypercubeAtlas
from atlas.topology_contract import TopologyContractViolation, TopologyWitness
from hypergraph.engine import Hypergraph
from sheaf.compat import LocalSection, Sheaf
from simplicial.complex import SimplicialComplex


def make_layers() -> TopologyWitness:
    atlas = HypercubeAtlas(dimensions=3)
    coordinates = (atlas.project({"axis_0": 1}),)

    hypergraph = Hypergraph()
    hypergraph.add(["a", "b", "c"], "declared")

    simplicial = SimplicialComplex()
    simplicial.add(["a", "b", "c"])

    sheaf = Sheaf()
    sheaf.add(LocalSection.create("local", {"state": "same"}))
    sheaf.add(LocalSection.create("local", {"state": "same", "detail": 1}))

    return TopologyWitness.from_layers(
        atlas_dimension=3,
        coordinates=coordinates,
        hypergraph=hypergraph,
        simplicial=simplicial,
        sheaf=sheaf,
    )


def test_topology_witness_is_deterministic_and_closed() -> None:
    left = make_layers()
    right = make_layers()

    assert left.verify()
    assert left.witness_id == right.witness_id
    assert left.canonical_payload() == right.canonical_payload()


def test_topology_witness_rejects_dimension_mismatch() -> None:
    try:
        TopologyWitness(atlas_dimension=2, coordinates=((0, 0, 0),), relations=(), simplices=())
    except TopologyContractViolation:
        return
    raise AssertionError("dimension mismatch was accepted")


def test_topology_witness_detects_simplex_without_declared_relation_nodes() -> None:
    witness = TopologyWitness(
        atlas_dimension=1,
        coordinates=((0,),),
        relations=((("a",), "only-a"),),
        simplices=(("a", "b"),),
    )
    assert not witness.verify()
