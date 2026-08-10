# Omega Canonical Architecture and Dataflow V2

> Status: architecture reconciliation draft; Gate B boundary and authority sequencing locked. Gate C is a broad system-archaeology and representation-validation phase, not a narrow TESSERACT-only implementation phase.

## Gate B boundary

```text
CorpusIdentity -> InformationSet -> ExperimentSpec -> ProvenanceManifest -> ExperimentResult
```

Every result is bound to the exact experiment and manifest identity. Result scope is explicit: `development`, `validation`, `holdout`, or `test`.

Only an explicitly `test`-scoped result may enter the final test spine. Development, validation, and holdout results cannot claim test authority.

## Canonical organism

Constitution -> Identity -> BentAxis -> Colony -> Runtime -> Evidence -> Experiment -> Atlas/TESSERACT -> Hypergraph -> Simplicial -> Sheaf -> TIAMAT -> ERK/Oracle -> Court -> E.N.D. -> Darwin's Pond -> bounded mutation -> L0 -> holdout/test firewall -> authority.

## TIAMAT

TIAMAT is the structural-dynamics layer with seven legal modes, M3 `[B,V,D]`, optional temporal memory, derived observables, explicit guard precedence, legal transitions, shared live/replay transition logic, canonical projection, and an M0-M7 identification registry with M7 permanent control.

Historical SimpleShock, LiveDeficit, RecoveryWeakness_v1, hazard_raw/hazard_score, hinge, richer state-update equations, refractory thresholds, promotion thresholds, and hysteresis remain evidence-classified until source provenance plus deterministic tests justify promotion. Historical diagnostic outputs remain `INCOMPARABLE` to probability-only evaluation unless a validated probability projection exists.

## Gate C scope: broad system archaeology

Gate C is not limited to TESSERACT. The entire library and historical corpus are to be searched and reconciled for every named system, interface, equation, threshold, state variable, guard, transition, artifact, wrapper, and experiment family that can materially constrain the canonical organism.

The active archaeology targets include, at minimum:

- Atlas / TESSERACT / circuit and topology semantics
- Hypergraph / Simplicial Complex / Sheaf representation and information-preserving composition
- TIAMAT state, modes, guards, transitions, replay, telemetry, projection, identification, SimpleShock, LiveDeficit, RecoveryWeakness, hazard, hinge, damage, recovery, residual load, momentum, refractory, promotion, hysteresis
- BentAxis / provenance / capsule / hash-chain / topology-state and authority metadata
- Runtime / Events / StateVector / Replay / Trajectory / Workers / ConstitutionalRecord
- Evidence / Experiment / calibration / diagnostic wrappers / probability-contract boundaries
- ERK / authority grants / signatures / revocation / replay protection
- Oracle / Adversary / UTV / Motif / Hazard / Hinge / Court
- E.N.D. / Darwin's Pond / mutation and holdout/test boundaries
- Historical artifacts, deleted wrappers, pull-request diffs, archived modules, notebooks, fixtures, tests, generated corpora, and documentation that may contain source-backed semantics

For every recovered item, record:

1. exact source artifact and provenance;
2. implementation location, if present;
3. semantic role and dependencies;
4. epistemic classification: canonical, derived, historical, experimental, control, or unresolved;
5. whether the current implementation agrees with the source;
6. missing equations, thresholds, transition rules, or metadata;
7. required deterministic/conformance tests;
8. whether promotion to runtime authority is justified.

## Representation validation

Gate C must establish whether the existing Atlas, Hypergraph, Simplicial, and Sheaf implementations preserve the same underlying information when composed. It must separately establish what TESSERACT contributes that cannot be inferred from generic topology. No representation is silently substituted for another.

This is a representation-validation task first. Boundary enforcement is added only after the canonical representation and its invariants are identified.

## TESSERACT rule

TESSERACT remains an unresolved historical implementation target, but it is not the sole Gate C target. Circuit semantics such as legal edges, energization, voltage/edge pull, impedance, conductance, capacitance, continuity, inductance, release gates, and power-test behavior must be traced to source evidence before implementation is treated as recovered canonical law.

## Verification order

1. Identity/canonical bytes
2. BentAxis provenance/history
3. Runtime replay determinism
4. Evidence/experiment/result boundary
5. Test-spine firewall
6. Broad library and corpus archaeology
7. Atlas/TESSERACT representation recovery
8. Hypergraph/Simplicial/Sheaf composition validation
9. TIAMAT structural dynamics and historical-law reconciliation
10. ERK/Oracle/Court
11. E.N.D.
12. Darwin's Pond

## Research rule

Never replace a missing layer with a convenient approximation. Preserve provenance and label partial, experimental, historical, or recovering concepts explicitly. Search the full available corpus before concluding that a semantic element is missing.

## Promotion rule

A historical claim becomes canonical only when its source artifact is identified, its epistemic classification is recorded, its deterministic implementation is tested, and replay/holdout behavior is conformance-checked. Absence from the current library is not evidence of absence from the historical corpus.
