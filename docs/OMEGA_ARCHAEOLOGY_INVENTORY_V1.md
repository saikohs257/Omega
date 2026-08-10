# Omega Archaeology Inventory V1

Status: ACTIVE RECONCILIATION

Purpose: prevent architectural drift by classifying every known Omega/TIAMAT-era subsystem before further implementation.

## Evidence baseline

The current repository contains explicit packages for BentAxis, Colony, Court, ERK, Hypergraph, Omega, Oracle, Runtime, Sheaf, Simplicial, and TIAMAT. The package manifest therefore confirms these as part of the present Omega surface.

## Classification

- PRESENT: code exists and has a recognizable role.
- PARTIAL: code exists, but current implementation is only a subset of the recovered design.
- RECOVER: historical/research material must be located before implementation.
- RECONCILE: multiple representations exist and must be assigned one canonical home.
- EXPERIMENTAL: useful research material that must not acquire authority automatically.
- DEPRECATED: retained for provenance but not part of the active architecture.
- OBSOLETE: should eventually be removed after provenance is preserved.

## Kernel and provenance

| Component | Status | Canonical role | Feeds |
|---|---|---|---|
| BentAxis Identity / canonical bytes | PRESENT / RECONCILE | immutable identity and canonical serialization | every artifact |
| BentAxis Store / HashChain | PRESENT | append-only evidence/provenance store | replay, lineage, audit |
| Runtime Event | PRESENT | atomic runtime event | BentAxis / trajectory |
| ConstitutionalRecord | PRESENT | kernel ABI/history record | replay |
| StateVector | PRESENT | immutable runtime state | replay / engines |
| ReplayRegistry / ReplayEngine | PRESENT / PARTIAL | deterministic reconstruction | verification / modules |
| Trajectory / workers | PRESENT / PARTIAL | runtime execution and traces | Colony / replay |

## Structural representation

| Component | Status | Canonical role | Feeds |
|---|---|---|---|
| Atlas | PRESENT / PARTIAL | coordinate/local-neighborhood representation | topology |
| TESSERACT / Hypercube | PRESENT / RECONCILE | legal topology and path structure | hypergraph / TIAMAT context |
| TESSERACT_CIRCUIT | RECOVER | circuit semantics: conductance, resistance, capacitance, continuity, release | future topology/runtime integration |
| Hypergraph | PRESENT / PARTIAL | higher-order relations | simplicial / context |
| Simplicial Complex | PRESENT / PARTIAL | higher-order geometric closure | sheaf / consistency |
| Sheaf | PRESENT / PARTIAL | local-section compatibility and global consistency | evidence/context |

## Research and reasoning engines

| Component | Status | Canonical role | Feeds |
|---|---|---|---|
| TIAMAT | PRESENT / PARTIAL | stateful structural dynamics and transition controller | diagnostics, ERK, Court, Oracle |
| TIAMAT identification registry | PRESENT | experiment-family registry and controls | identification runner |
| TIAMAT historical runtime rules | PRESENT / EXPERIMENTAL | recovered/shadow authority logic | runtime validation |
| ERK | PRESENT / RECONCILE | evidence/risk kernel | Court / runtime authority |
| Oracle | PRESENT / PARTIAL | adversarial inference/challenge | experiments / Court |
| Adversary | RECOVER | explicit challenge/counterexample layer | Oracle / UTV |
| UTV (Undertow/Turbulence/Vortex) | RECOVER | escalation/adversarial trajectory model | Oracle / Court |
| Motif Engine | RECOVER | recurring structural pattern representation | Oracle / E.N.D. / Pond |
| Hazard Kernel | RECOVER / RECONCILE | hazard-specific evidence/state computation | TIAMAT/ERK boundary must be resolved |
| Hinge | RECOVER / RECONCILE | transition/hinge pressure diagnostic | TIAMAT / Oracle |

## Selection and evolution

| Component | Status | Canonical role | Feeds |
|---|---|---|---|
| Court | PRESENT / PARTIAL | formal survival/elimination/adjudication | E.N.D. on failure; lineage on survival |
| E.N.D. | PRESENT / PARTIAL | immutable failure analysis | Darwin's Pond |
| Darwin's Pond | PRESENT / PARTIAL | immutable hypothesis reservoir and bounded mutation | new hypothesis at L0 |
| Failure genes | EXPERIMENTAL | recurring cross-lineage failure patterns | E.N.D. scrutiny only |
| Resurrection | EXPERIMENTAL | explicit descendant under changed assumptions | fresh L0 experiment |
| Merge/recombination | DEFERRED | future lineage operation | not active |

## Evidence and experimentation

| Component | Status | Canonical role | Feeds |
|---|---|---|---|
| Canonical corpus identity | PARTIAL / RECOVER | exact evidence definition | information set |
| Information-set contract | PARTIAL / RECOVER | what a hypothesis may see | experiment |
| Experiment contract | PARTIAL / RECOVER | hypothesis + evidence + metric + implementation identity | replay / result |
| Diagnostic runner | PRESENT / PARTIAL | canonical experiment execution | calibration / Court |
| Probability contract | PRESENT / PARTIAL | distinguish probabilities from scores/diagnostics | calibration / comparison |
| Calibration/report artifacts | PRESENT / PARTIAL | probabilistic evaluation | Court |
| Historical TIAMAT probability adapter | FORBIDDEN | would contaminate historical baseline | none |

## Validation and firewalls

| Component | Status | Canonical role |
|---|---|---|
| Historical replay | PRESENT / PARTIAL | behavioral reconstruction |
| Chronological holdout | PRESENT / PARTIAL | temporal generalization |
| Regime holdout | PARTIAL / RECOVER | regime robustness |
| Source/path holdout | PARTIAL / RECOVER | source independence |
| Test-spine firewall | RECOVER / IMPLEMENT | prevent evolutionary leakage |
| Authority firewall | PRESENT / PARTIAL | prevent evidence from becoming unauthorized action |
| Deterministic replay/conformance | PRESENT / PARTIAL | exact repeatability |
| Provenance audit | PRESENT / PARTIAL | evidence lineage |

## Canonical dependency order

1. Constitution and package boundaries.
2. Identity and canonical bytes.
3. BentAxis storage, provenance, and hash chain.
4. Runtime events, constitutional records, state vector, trajectory, replay registry, deterministic replay.
5. Canonical corpus and information-set identity.
6. Experiment contract and metric/probability contracts.
7. Atlas/TESSERACT topology.
8. Hypergraph and simplicial representations.
9. Sheaf/context consistency.
10. TIAMAT structural state, dynamics, guards, modes, replay, identification.
11. ERK evidence/risk projections.
12. Oracle and recovered adversarial/UTV machinery.
13. Diagnostic runner and calibration/comparison.
14. Court adjudication.
15. E.N.D. failure diagnosis.
16. Darwin's Pond bounded mutation/lineage.
17. Test-spine and authority firewalls enforced across the entire loop.
18. Cross-module conformance and end-to-end replay.

## Feed graph

```text
SOURCE / CORPUS
      |
      v
CANONICAL IDENTITY + INFORMATION SET
      |
      v
EXPERIMENT CONTRACT
      |
      v
RUNTIME / REPLAY KERNEL
      |
      +----> BENTAXIS provenance
      |
      v
ATLAS / TESSERACT
      |
      +----> HYPERGRAPH
      |          |
      |          v
      |     SIMPLICIAL
      |          |
      |          v
      |        SHEAF
      |
      v
TIAMAT
  |      |       |
  |      |       +----> ORACLE / ADVERSARY / UTV
  |      |
  |      +------------> ERK
  |
  +-------------------> diagnostics / probability projection
                              |
                              v
                            COURT
                         /           \
                     SURVIVE         FAIL
                       |               |
                       v               v
                    LINEAGE          E.N.D.
                                       |
                                       v
                              DARWIN'S POND
                                       |
                              SNIP / ALTER / HOLD
                                       |
                                       v
                                  NEW HYPOTHESIS
                                       |
                                      L0
```

## Rules for unresolved historical modules

1. Do not implement from memory when a historical artifact may exist.
2. Do not create a second package for a concept until its canonical home is established.
3. Do not promote an experimental module to runtime authority because it improves a benchmark.
4. Preserve historical failures and hypotheses even when they are eliminated.
5. Keep the final test spine outside E.N.D., Darwin's Pond, mutation generation, and diagnostic tuning.
6. Every module must declare its inputs, outputs, authority level, provenance requirements, and replay semantics.
7. Every recovered equation or rule receives an epistemic label: OBSERVED, DERIVED, INFERRED, HYPOTHESIZED, CONFIRMED, FALSIFIED, or UNRESOLVED.

## Immediate implementation sequence

### Gate A — Kernel
- verify canonical bytes and identity consistency
- verify BentAxis append/replay/hash-chain invariants
- verify deterministic runtime replay

### Gate B — Evidence
- define corpus and information-set identities
- define experiment record and metric contract
- lock test-spine boundaries

### Gate C — Structural engines
- reconcile Atlas/TESSERACT/Hypergraph/Simplicial/Sheaf
- document exactly which representation feeds which downstream module

### Gate D — TIAMAT
- line-by-line reconcile historical specification against current implementation
- recover missing equations, timers, guards, transitions, and projections only from evidence

### Gate E — Reasoning and adjudication
- reconcile ERK / Oracle / Adversary / UTV / Motif / Hazard / Hinge
- implement Court after the evidence and prediction contracts are stable

### Gate F — Evolution
- complete E.N.D. tests and Pond tests
- enforce precommitted mutation proposals, budgets, quarantine, and L0 restart

### Gate G — Whole-system proof
- historical replay
- chronological holdout
- regime/source/path holdouts
- deterministic replay
- provenance verification
- test-spine isolation
- authority firewall
- end-to-end conformance

## Current conclusion

Omega is not missing one feature. It is missing a completed, verified connection between several already-existing subsystems and several historically important subsystems whose canonical implementations still need recovery.

The next work should therefore be dependency-driven archaeology and reconciliation, not feature accumulation.
