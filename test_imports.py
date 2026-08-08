"""Test that all modules import correctly."""
from __future__ import annotations

import sys
import traceback

def test_imports():
    """Attempt to import all modules and report errors."""
    
    modules_to_test = [
        # Runtime
        ("runtime.events", "Event"),
        ("runtime.operators", "Operator", "IdentityOperator", "AnnotateOperator"),
        ("runtime.trajectory", "Trajectory"),
        ("runtime.workers", "Worker", "WorkerTrace"),
        ("runtime.replay", "ReplayEngine", "ReplayResult"),
        
        # BentAxis (core substrate)
        ("bentaxis.identity", "Identity", "to_canonical_bytes"),
        ("bentaxis.hashchain", "HashChain"),
        ("bentaxis.store", "BentAxisStore", "StoredEvent"),
        ("bentaxis.provenance", "ProvenanceGraph", "ProvenanceEdge"),
        ("bentaxis.capsule", "BentAxisCapsule"),
        
        # Colony
        ("colony.scheduler", "ColonyScheduler", "ColonyRoundResult"),
        
        # Court
        ("court.engine", "Court", "Verdict"),
        
        # TIAMAT
        ("tiamat.engine", "TiamatEngine", "Decision"),
        
        # Oracle
        ("oracle.engine", "Oracle", "Amendment"),
        
        # Atlas
        ("atlas.interface", "Atlas", "AtlasNeighborhood"),
        ("atlas.hypercube", "HypercubeAtlas"),
        
        # Hypergraph
        ("hypergraph.engine", "Hyperedge", "Hypergraph"),
        
        # Sheaf
        ("sheaf.compat", "Sheaf", "LocalSection"),
        
        # Simplicial
        ("simplicial.complex", "Simplex", "SimplicialComplex"),
    ]
    
    errors = []
    passed = 0
    
    for test_spec in modules_to_test:
        module_name = test_spec[0]
        exports = test_spec[1:]
        
        try:
            module = __import__(module_name, fromlist=exports)
            
            for export in exports:
                if not hasattr(module, export):
                    errors.append(f"❌ {module_name}: Missing export '{export}'")
                else:
                    passed += 1
                    print(f"✅ {module_name}.{export}")
        except Exception as e:
            errors.append(f"❌ {module_name}: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(errors)}")
    
    if errors:
        print(f"\nErrors found:")
        for error in errors:
            print(error)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(test_imports())
