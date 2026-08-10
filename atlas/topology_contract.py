from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from bentaxis.identity import Identity
from hypergraph.engine import Hypergraph
from sheaf.compat import Sheaf
from simplicial.complex import SimplicialComplex


class TopologyContractViolation(ValueError):
    """Raised when an explicit topology reconciliation witness is inconsistent."""


@dataclass(frozen=True, slots=True)
class TopologyWitness:
    """Evidence-only bridge across Atlas/TESSERACT topology layers.

    This object deliberately carries declarations rather than inventing historical
    semantics. A witness is valid only when the declared hypergraph relations,
    simplices, and local sections agree with one another.
    """

    atlas_dimension: int
    coordinates: tuple[tuple[int, ...], ...]
    relations: tuple[tuple[tuple[str, ...], str], ...]
    simplices: tuple[tuple[str, ...], ...]
    sections: tuple[tuple[str, tuple[tuple[str, object], ...]], ...] = ()
    witness_id: str = ""

    def __post_init__(self) -> None:
        if self.atlas_dimension < 0:
            raise TopologyContractViolation("atlas_dimension must be non-negative")
        if any(len(coordinate) != self.atlas_dimension for coordinate in self.coordinates):
            raise TopologyContractViolation("all coordinates must match atlas_dimension")
        payload = {
            "atlas_dimension": self.atlas_dimension,
            "coordinates": self.coordinates,
            "relations": self.relations,
            "simplices": self.simplices,
            "sections": self.sections,
        }
        object.__setattr__(self, "witness_id", Identity.calculate(payload).digest)

    @classmethod
    def from_layers(
        cls,
        *,
        atlas_dimension: int,
        coordinates: Iterable[tuple[int, ...]],
        hypergraph: Hypergraph,
        simplicial: SimplicialComplex,
        sheaf: Sheaf | None = None,
    ) -> "TopologyWitness":
        relations = tuple(
            sorted((tuple(sorted(edge.nodes)), edge.label) for edge in hypergraph.edges)
        )
        simplex_vertices = tuple(
            sorted(tuple(sorted(simplex.vertices)) for simplex in simplicial.maximal_simplices())
        )
        sections = ()
        if sheaf is not None:
            sections = tuple(
                sorted((section.domain, tuple(section.values)) for section in sheaf.sections)
            )
        return cls(
            atlas_dimension=atlas_dimension,
            coordinates=tuple(coordinates),
            relations=relations,
            simplices=simplex_vertices,
            sections=sections,
        )

    def verify(self) -> bool:
        """Verify internal closure without assigning unproven historical meaning."""
        node_sets = {node for nodes, _ in self.relations for node in nodes}
        simplex_nodes = {node for simplex in self.simplices for node in simplex}
        if not simplex_nodes.issubset(node_sets):
            return False
        section_domains = {domain for domain, _ in self.sections}
        if len(section_domains) != len(self.sections):
            # Multiple sections may share a domain; compatibility is the actual check.
            pass
        sheaf = Sheaf()
        for domain, values in self.sections:
            from sheaf.compat import LocalSection

            sheaf.add(LocalSection(domain=domain, values=values))
        return sheaf.compatibility()

    def canonical_payload(self) -> Mapping[str, object]:
        return {
            "atlas_dimension": self.atlas_dimension,
            "coordinates": self.coordinates,
            "relations": self.relations,
            "simplices": self.simplices,
            "sections": self.sections,
            "witness_id": self.witness_id,
        }
