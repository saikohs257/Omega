# Omega Canonical Architecture and Dataflow V2

> Status: architecture reconciliation draft. This file records the current best ordering of the Omega organism from repository evidence, historical TIAMAT notes, and the recovered failure-analysis layers. It distinguishes present modules from missing, partial, and still-recovering concepts.

## Gate B boundary addendum

The evidence-to-result boundary is now explicit:

```text
CorpusIdentity
  -> InformationSet
  -> ExperimentSpec
  -> ProvenanceManifest
  -> ExperimentResult
```

Every result is bound to the exact experiment identity and manifest identity. Result scope is explicit: `development`, `validation`, `holdout`, or `test`.

Only an explicitly `test`-scoped `ExperimentResult` may enter the final test spine. Development, validation, and holdout results cannot claim test authority through the result boundary.

TIAMAT remains a structural-dynamics subsystem. Historical diagnostic outputs remain `INCOMPARABLE` to probability-only evaluation until a validated probability projection is explicitly established.

The TIAMAT reconciliation ledger is `docs/TIAMAT_CLAIM_LEDGER_V1.md`. Historical equations, thresholds, hysteresis rules, or guard semantics are not promoted merely because they appear in recovered notes; promotion requires source provenance plus deterministic implementation and tests.

## Core rule

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

## Canonical order of the organism

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

## What feeds what

The established feed order remains:

```text
Constitution -> Identity -> BentAxis -> Runtime/Evidence
 -> Experiment -> Atlas/TESSERACT -> Hypergraph
 -> Simplicial -> Sheaf -> TIAMAT -> ERK/Oracle
 -> Court -> E.N.D. -> Darwin’s Pond -> L0
 -> Holdout/Test firewall -> Authority
```

TIAMAT consumes structural context and evidence trajectories. Its canonical runtime surface is the M3 `[B,V,D]` state with optional `tau_D` and `tau_mode`, derived recovery/pressure/momentum/residual-load observables, explicit guards, legal transitions, and shared live/replay transition logic.

## Present modules

The repository contains the canonical substrate/runtime layers plus the current TIAMAT, ERK, Oracle, Court, topology, and failure-analysis components. The remaining archaeological work is to reconcile partial implementations with historical evidence rather than invent substitutes.

## Verification order

1. Canonical bytes and identity
2. BentAxis provenance and append-only history
3. Runtime replay determinism
4. Evidence/experiment/result boundary
5. Test-spine firewall
6. Atlas / hypergraph / simplicial / sheaf consistency
7. TIAMAT structural dynamics
8. ERK / Oracle / Court boundaries
9. E.N.D. failure diagnosis
10. Darwin’s Pond bounded evolution

## Explicit research rule

Never replace a missing layer with a convenient approximation unless the approximation is clearly labeled as partial or experimental.

Every missing item should be tagged as one of:

- PRESENT
- PARTIAL
- MISSING
- MISPLACED
- OBSOLETE
- RECOVERING
