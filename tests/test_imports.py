"""Package import smoke tests for the wheel-installed runtime."""

from __future__ import annotations

import importlib


MODULE_EXPORTS = (
    ("runtime.events", ("Event",)),
    ("runtime.operators", ("Operator", "IdentityOperator", "AnnotateOperator")),
    ("runtime.trajectory", ("Trajectory",)),
    ("runtime.workers", ("Worker", "WorkerTrace")),
    ("runtime.replay", ("ReplayEngine", "ReplayResult")),
    ("bentaxis.identity", ("Identity", "to_canonical_bytes")),
    ("bentaxis.hashchain", ("HashChain",)),
    ("bentaxis.store", ("BentAxisStore", "StoredEvent")),
    ("bentaxis.provenance", ("ProvenanceGraph", "ProvenanceEdge")),
    ("bentaxis.capsule", ("BentAxisCapsule",)),
    ("colony.scheduler", ("ColonyScheduler", "ColonyRoundResult")),
    ("court.engine", ("Court", "Verdict")),
    ("tiamat.engine", ("TiamatEngine", "Decision")),
    ("oracle.engine", ("Oracle", "Amendment")),
    ("atlas.interface", ("Atlas", "AtlasNeighborhood")),
    ("atlas.hypercube", ("HypercubeAtlas",)),
    ("hypergraph.engine", ("Hyperedge", "Hypergraph")),
    ("sheaf.compat", ("Sheaf", "LocalSection")),
    ("simplicial.complex", ("Simplex", "SimplicialComplex")),
)


def test_public_package_exports_import_from_built_wheel() -> None:
    missing: list[str] = []
    for module_name, exports in MODULE_EXPORTS:
        module = importlib.import_module(module_name)
        missing.extend(
            f"{module_name}.{export}"
            for export in exports
            if not hasattr(module, export)
        )
    assert not missing, f"missing public exports: {missing}"
