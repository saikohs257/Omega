# Omega

Canonical runtime for the Omega constitutional organism.

## ERK Constitutional Runtime

The `erk/` package contains the Epistemic Runtime Kernel reference boundary.

Core separation:

```text
Plant -> telemetry -> Observer -> epistemic state
                              |
                              v
                    Constitutional Kernel
                              |
                              v
                         Supervisor
                              |
                              v
                         Transition
                              |
                              v
                           Replay
```

The Constitutional Kernel is the only supported boundary for applying policy actions to runtime state. It rejects inadmissible actions, preserves evidence-count monotonicity, consumes execution authority after execution, and provides deterministic replay hashing.

### Current constitutional tests

- adversarial authority and evidence tests
- transition-kernel tests
- metamorphic determinism tests
- exact threshold boundary tests

CI executes the complete ERK suite on `erk-v22-fix` and pull requests targeting `main`.

## Legacy Build Order

1. BentAxis
2. Colony
3. Atlas (TESSERACT)
4. Hypergraph
5. Simplicial Complex
6. Sheaf
7. TIAMAT
8. Court
9. Oracle

Rule: No direct worker-to-worker communication. All coordination occurs through BentAxis (stigmergic traces).
