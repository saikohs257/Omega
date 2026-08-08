"""Verify the public package surface imports from an installed checkout."""
from __future__ import annotations

import importlib

import pytest


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


@pytest.mark.parametrize(("module_name", "exports"), MODULE_EXPORTS)
def test_public_module_exports_import(module_name: str, exports: tuple[str, ...]) -> None:
    module = importlib.import_module(module_name)
    missing = [name for name in exports if not hasattr(module, name)]
    assert not missing, f"{module_name} is missing exports: {missing}"
