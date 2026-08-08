# Omega

Canonical runtime for the Omega constitutional organism.

## Repository status

The repository contains one canonical implementation line. Obsolete TIAMAT scaffold notes and superseded integration scaffolds are not part of `main`.

### Canonical build order
1. BentAxis
2. Colony
3. Atlas (TESSERACT)
4. Hypergraph
5. Simplicial Complex
6. Sheaf
7. TIAMAT
8. Court
9. Oracle

### TIAMAT status

TIAMAT's runtime surface is explicit and deterministic:

- seven-mode state machine: `Q → P → E → C → H → R → Rf`
- primary reduced state: `M3 = [B, V, D]`
- optional temporal state: `tau_D`, `tau_mode`
- derived observables: recovery, pressure, momentum, residual load
- explicit guard evaluation and legal transition table
- shared live/replay transition function
- canonical telemetry projection
- M0–M7 identification registry with M7/V6 retained as the permanent control
- deterministic temporal train/validation/test holdout evaluation

The identification layer is an evaluation surface, not a second runtime. Empirical dynamics are only promoted into canonical runtime behavior when supported by replay/holdout evidence; the repository does not silently encode unverified equations as facts.

The retired fixed six-hour choke timer is not part of canonical runtime logic.

## Coordination rule

No direct worker-to-worker communication. All coordination occurs through BentAxis (stigmergic traces).

## Completion rule

`main` is the canonical source of truth. Historical/superseded branches may remain on GitHub for provenance, but they are not implementation authorities. Changes must converge on the current canonical runtime and its tests rather than preserving parallel scaffolds.
