# Omega Canonical Architecture and Dataflow V2

> Status: architecture reconciliation draft. This file records the current best ordering of the Omega organism from repository evidence, historical TIAMAT notes, and the recovered failure-analysis layers. It distinguishes present modules from missing, partial, and still-recovering concepts.

## Gate B boundary addendum

The evidence-to-result boundary is now explicit:

```text
CorpusIdentity -> InformationSet -> ExperimentSpec -> ProvenanceManifest -> ExperimentResult
```

Every result is bound to the exact experiment identity and manifest identity. Result scope is explicit: development, validation, holdout, or test.

Only an explicitly `test`-scoped `ExperimentResult` may enter the final test spine. Development, validation, and holdout results cannot claim test authority through the result boundary.

TIAMAT remains a structural-dynamics subsystem. Historical diagnostic outputs remain `INCOMPARABLE` to probability-only evaluation until a validated probability projection is explicitly established.

The TIAMAT reconciliation ledger is `docs/TIAMAT_CLAIM_LEDGER_V1.md`. Historical equations, thresholds, hysteresis rules, or guard semantics are not promoted merely because they appear in recovered notes; promotion requires source provenance plus deterministic implementation and tests.

## Core rule

Omega is not one model. It is a layered organism.

Each layer must feed the next without collapsing its semantics into the next layer’s job.

- Identity identifies.
- BentAxis preserves provenance and canonical bytes.
- Colony schedules and executes worker rounds.
- Atlas / Hypergraph / Simplicial / Sheaf transform state into progressively richer structural representations.
- TIAMAT models structural dynamics and mode transitions.
- ERK evaluates evidence/risk/kernel semantics.
- Oracle challenges claims and generates adversarial pressure.
- Court adjudicates survival versus failure under the experiment contract.
- E.N.D. diagnoses failure.
- Darwin’s Pond preserves failed lineages and proposes bounded descendants.

## Canonical order

Constitution -> Identity -> BentAxis -> Colony -> Runtime -> Evidence -> Experiment -> Atlas/TESSERACT -> Hypergraph -> Simplicial -> Sheaf -> TIAMAT -> ERK -> Oracle -> Court -> E.N.D. -> Darwin's Pond -> bounded mutation -> L0 -> holdout/test firewall -> authority.

## TIAMAT boundary

TIAMAT consumes structural context, local compatibility, temporal memory, and evidence trajectories. Its canonical runtime surface is:

- M3 primary state `[B,V,D]`
- optional temporal state `tau_D`, `tau_mode`
- derived recovery, pressure, momentum, residual load
- explicit guard evaluation
- legal mode transition table
- shared live/replay transition function
- canonical state projection
- M0-M7 identification registry with M7 permanent control

TIAMAT must not be reduced to a probability scalar and identification must not become a second runtime.

## Archaeological boundary

Historical concepts including SimpleShock, LiveDeficit, RecoveryWeakness_v1, hazard_raw/hazard_score, hinge, richer damage/recovery/residual-load/momentum laws, refractory thresholds, promotion thresholds, and hysteresis remain evidence-classified until source provenance and deterministic tests justify promotion.

## Verification order

1. Canonical bytes and identity
2. BentAxis provenance and append-only history
3. Runtime replay determinism
4. Evidence/experiment/result boundary
5. Test-spine firewall
6. Atlas / Hypergraph / Simplicial / Sheaf consistency
7. TIAMAT structural dynamics
8. ERK / Oracle / Court boundaries
9. E.N.D. failure diagnosis
10. Darwin’s Pond bounded evolution

## Explicit research rule

Never replace a missing layer with a convenient approximation unless the approximation is clearly labeled as partial or experimental. Missing concepts are tagged PRESENT, PARTIAL, MISSING, MISPLACED, OBSOLETE, or RECOVERING.
