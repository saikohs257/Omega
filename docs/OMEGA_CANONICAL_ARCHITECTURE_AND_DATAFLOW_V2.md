# Omega Canonical Architecture and Dataflow V2

> Status: architecture reconciliation draft. This file records the current best ordering of the Omega organism from repository evidence, historical TIAMAT notes, and the recovered failure-analysis layers. It distinguishes present modules from missing, partial, and still-recovering concepts.

## 1. Core rule

Omega is not one model. It is a layered organism.

Each layer must feed the next without collapsing its semantics into the next layer’s job.

- **Identity** identifies.
- **BentAxis** preserves provenance and canonical bytes.
- **Colony** schedules and executes worker rounds.
- **Atlas / Hypergraph / Simplicial / Sheaf** transform state into progressively richer structural representations.
- **TIAMAT** models structural dynamics and mode transitions.
- **ERK** evaluates evidence/risk/kernel semantics.
- **Oracle** challenges claims and generates adversarial pressure.
- **Court** adjudicates survival versus failure under the experiment contract.
- **E.N.D.** diagnoses failure.
- **Darwin’s Pond** preserves failed lineages and proposes bounded descendants.

A component may feed multiple downstream layers, but each downstream layer must keep its own authority boundary.

## 2. Canonical order of the organism

1. **Constitution**
2. **Identity / canonical bytes**
3. **BentAxis**
4. **Colony**
5. **Runtime kernel**
6. **Evidence / corpus / information set**
7. **Experiment contract**
8. **Atlas / TESSERACT**
9. **Hypergraph**
10. **Simplicial complex**
11. **Sheaf**
12. **TIAMAT**
13. **ERK**
14. **Oracle**
15. **Court**
16. **E.N.D.**
17. **Darwin’s Pond**
18. **Bounded mutation / descendant generation**
19. **L0 re-entry**
20. **Holdout / test-spine firewall / final authority**

## 3. What feeds what

### 3.1 Constitution → Identity

The constitution defines what kinds of records, provenance, replay, and authority the organism is allowed to have.

Identity then turns arbitrary structures into canonical bytes and immutable digests.

### 3.2 Identity → BentAxis

BentAxis stores canonicalized events, content identities, and hash-linked provenance.

Current evidence shows BentAxis uses:

- `Identity.calculate(...)`
- `HashChain`
- immutable stored events
- append-only store snapshots

BentAxis is the provenance substrate, not a model.

### 3.3 BentAxis → Colony

Colony consumes state mappings and worker traces.

The current scheduler runs registered workers sequentially and returns a new state plus traces.

That means Colony is the worker-execution layer that sits above the BentAxis history substrate.

### 3.4 BentAxis / Runtime → Replay kernel

The runtime layer reconstructs constitutional records into state vectors.

Observed flow:

- `ConstitutionalRecord` is the ABI record primitive.
- `ReplayRegistry` resolves record-specific reconstruction operators.
- `ReplayEngine` walks records and reconstructs `StateVector`.
- `StateVector` is the immutable reconstructed state container.

This is the deterministic replay spine.

### 3.5 Runtime → Atlas / TESSERACT

Atlas provides the coordinate interface.

A state is projected into a coordinate tuple, charted, and compared with local neighborhoods.

Current implementation is a hypercube projection interface, so Atlas is the topological coordinate layer, not yet the full recovered circuit model.

### 3.6 Atlas → Hypergraph

Atlas gives coordinates; Hypergraph gives higher-order relations among named nodes.

Hypergraph is the next step when state must be represented as relation sets instead of only coordinates.

### 3.7 Hypergraph → Simplicial complex

Simplicial complex preserves face closure and maximal simplices.

Use this when the architecture needs to reason about higher-order co-membership and overlapping structure rather than only pairwise or hyperedge relationships.

### 3.8 Simplicial → Sheaf

Sheaf checks local compatibility across overlapping domains and builds global sections when the local views agree.

This is the consistency layer for heterogeneous local evidence.

### 3.9 Sheaf → TIAMAT

TIAMAT consumes structural context, local compatibility, temporal memory, and evidence trajectories.

TIAMAT is the structural-dynamics engine:

- primary reduced state: `M3 = [B, V, D]`
- optional temporal state: `tau_D`, `tau_mode`
- derived observables: recovery, pressure, momentum, residual load
- explicit guards and legal mode transitions
- shared live/replay transition logic
- canonical projection of state

TIAMAT should not be reduced to a probability scalar.

### 3.10 TIAMAT → ERK

TIAMAT’s structural state can feed ERK, which evaluates evidence/risk consequences and kernel semantics.

ERK should remain distinct from TIAMAT’s internal dynamics.

### 3.11 TIAMAT → Oracle

Oracle receives the structural claim and pressure-tests it.

Oracle is the adversarial challenge layer: counterexample generation, disagreement pressure, and alternative explanations.

### 3.12 Oracle → Court

Court receives the experiment under challenge and determines survival, abstention, or failure under the current evaluation contract.

Court must not diagnose failure; it adjudicates only.

### 3.13 Court → E.N.D.

When Court records failure, E.N.D. receives the immutable evidence and produces a failure diagnosis.

E.N.D. does not alter evidence or hypotheses.

### 3.14 E.N.D. → Darwin’s Pond

E.N.D. produces the diagnosed failure record, taxonomy, certainty level, and suspected defect structure.

Darwin’s Pond stores the failed lineage, mutation proposal, and bounded descendant metadata.

### 3.15 Darwin’s Pond → bounded mutation → L0

Darwin’s Pond can propose a bounded new hypothesis via:

- SNIP
- ALTER
- HOLD

Any descendant is a new identity and starts from L0.

## 4. Present modules in the repository

### Present and explicit

- `bentaxis/identity.py`
- `bentaxis/store.py`
- `bentaxis/hashchain.py`
- `bentaxis/provenance.py`
- `runtime/constitutional_record.py`
- `runtime/events.py`
- `runtime/state_vector.py`
- `runtime/replay_registry.py`
- `runtime/replay.py`
- `runtime/workers.py`
- `atlas/interface.py`
- `atlas/hypercube.py`
- `hypergraph/engine.py`
- `simplicial/complex.py`
- `sheaf/compat.py`
- `colony/scheduler.py`
- `tiamat/state.py`
- `tiamat/modes.py`
- `tiamat/guards.py`
- `tiamat/transition.py`
- `tiamat/replay.py`
- `tiamat/projection.py`
- `tiamat/identification_registry.py`
- `tiamat/engine.py`
- `court/engine.py`
- `oracle/engine.py`
- `erk/kernel.py`
- `erk/runtime.py`
- `docs/TIAMAT_RECONCILIATION_V1.md`
- `docs/TIAMAT_INTERFACE_BOUNDARY_V1.md`
- `docs/END_DARWINS_POND_V1.md`

### Partial or conceptually incomplete

- Atlas is currently an interface + hypercube implementation, not the fully recovered TESSERACT/circuit model.
- TIAMAT is present, but the top-level engine still needs reconciliation against the fuller recovered structural controller.
- Oracle, Court, and ERK exist, but the historical adversary/motif/UTV/hazard-hinge lineage still needs explicit mapping.
- Colony exists as a scheduler, but its full constitutional role needs reconciliation against the broader runtime/worker model.
- Sheaf exists as compatibility logic, but its intended role in the full organism needs to be reconciled with the historical corpus.

### Missing or still to be recovered

- Adversary / UTV / Motif Engine / Hazard Kernel / Hinge as explicit modules or explicit sublayers
- Full TESSERACT / circuit semantics beyond the current Atlas hypercube interface
- Canonical corpus generator and historical forward-panel reconstruction pipeline
- Final test-spine firewall implementation details
- A single universal experiment contract that every runtime layer uses
- A complete claim/probability/calibration boundary specification

## 5. Current dataflow spine

```text
Corpus / evidence
    ↓
Information set
    ↓
Experiment contract
    ↓
Replay / runtime kernel
    ↓
Structural layers (Atlas → Hypergraph → Simplicial → Sheaf)
    ↓
TIAMAT
    ↓
ERK / Oracle
    ↓
Court
    ↓
PASS → lineage
FAIL → E.N.D. → Darwin’s Pond → bounded mutation
    ↓
L0 re-entry
```

## 6. Verification order

The order of verification should follow the feed order:

1. Canonical bytes and identity
2. BentAxis provenance and append-only history
3. Runtime replay determinism
4. Atlas / hypergraph / simplicial / sheaf consistency
5. TIAMAT structural dynamics
6. ERK / Oracle / Court boundaries
7. E.N.D. failure diagnosis
8. Darwin’s Pond bounded evolution
9. Test-spine firewall and authority firewall

If a downstream layer is implemented before its upstream feed is canonical, the architecture becomes hard to trust.

## 7. Explicit research rule

Never replace a missing layer with a convenient approximation unless the approximation is clearly labeled as partial or experimental.

Every missing item should be tagged as one of:

- PRESENT
- PARTIAL
- MISSING
- MISPLACED
- OBSOLETE
- RECOVERING

This document should be updated as the archaeology pass continues.
