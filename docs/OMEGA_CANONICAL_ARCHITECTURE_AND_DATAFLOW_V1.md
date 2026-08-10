# Omega Canonical Architecture and Dataflow

**Version:** v1.0
**Status:** Architecture Freeze Candidate
**Purpose:** Reconcile the complete Omega organism, recover historically important subsystems, define dependency order, define module boundaries, and specify what feeds what.

---

## 1. Executive Decision

Omega is not a collection of independent predictors. It is a deterministic constitutional organism whose modules have different epistemic jobs.

The canonical architecture must preserve and integrate the major subsystems already developed across the Omega/TIAMAT work rather than replacing them with a smaller recent stack.

The architecture is organized into five planes:

1. **Substrate / representation** — BentAxis, Identity, canonical bytes, provenance, hash chain.
2. **Structure / context** — Colony, Atlas/TESSERACT, Hypergraph, Simplicial Complex, Sheaf.
3. **Runtime / mechanisms** — Runtime kernel and TIAMAT.
4. **Challenge / adjudication** — ERK, Oracle, Adversary/UTV, Court.
5. **Failure / evolution / memory** — E.N.D. and Darwin's Pond.

A sixth cross-cutting plane enforces constitutional safety:

- corpus and information-set identity
- experiment contracts
- probability/calibration contracts
- replay and determinism
- holdout/test-spine isolation
- provenance
- authority firewall
- conformance verification

No module may silently absorb another module's constitutional role.

---

## 2. Canonical Dependency Order

The build order is:

```text
CONSTITUTION
    |
    v
IDENTITY / CANONICAL BYTES
    |
    v
BENTAXIS
    |
    +--------------------+
    |                    |
    v                    v
COLONY               EVIDENCE / CORPUS
    |                    |
    v                    v
RUNTIME KERNEL      INFORMATION SET
    |                    |
    +---------+----------+
              |
              v
        ATLAS / TESSERACT
              |
              v
          HYPERGRAPH
              |
              v
      SIMPLICIAL COMPLEX
              |
              v
             SHEAF
              |
              v
           TIAMAT
              |
       +------+------+
       |             |
       v             v
      ERK          ORACLE
       |             |
       |          ADVERSARY
       |             |
       |            UTV
       |             |
       +------+------+
              |
              v
            COURT
              |
        +-----+-----+
        |           |
      PASS         FAIL
        |           |
        |           v
        |          E.N.D.
        |           |
        |      DARWIN'S POND
        |           |
        |      bounded descendant
        |           |
        |           v
        |          L0
        |           |
        +-----------+
                    |
                    v
                 REPLAY
                    |
                    v
              HOLDOUT / TEST
                    |
                    v
                AUTHORITY
```

This is a logical dependency order, not a requirement that every package be implemented from scratch in exactly this sequence. Existing implementations must be audited and connected to this architecture.

---

# 3. Constitutional Layer

## 3.1 Constitution

The Constitution is the highest-level authority.

It defines non-negotiable rules concerning:

- immutable evidence
- deterministic execution
- provenance
- authority boundaries
- test-spine isolation
- historical preservation
- canonical implementation status
- no silent mutation
- no worker-to-worker communication outside approved substrate

The repository already contains `CONSTITUTION.md`.

### Feeds

Constitution -> every module's legal operating constraints.

### Must never receive

No runtime result may rewrite the Constitution automatically.

---

# 4. Identity and Canonical Serialization

## 4.1 Identity

Every durable object needs a stable identity:

- hypothesis
- experiment
- corpus
- information set
- implementation
- state
- event
- diagnosis
- mutation proposal
- result
- artifact

Canonical serialization must precede hashing.

Conceptual rule:

```text
object
  -> canonical bytes
  -> content hash
  -> immutable identity
```

## 4.2 Why this is foundational

Without one identity system, two modules can believe they are referring to the same experiment while actually referring to different inputs or implementations.

### Feeds

Identity -> BentAxis
Identity -> experiment contracts
Identity -> replay
Identity -> E.N.D.
Identity -> Darwin's Pond
Identity -> Court
Identity -> Oracle

---

# 5. BentAxis — Substrate and Provenance

BentAxis is the canonical substrate, not an intelligence layer.

Existing pieces include:

- `bentaxis/store.py`
- `bentaxis/capsule.py`
- `bentaxis/hashchain.py`
- `bentaxis/provenance.py`

## Responsibilities

BentAxis provides:

- immutable storage
- content-addressed artifacts
- canonical provenance
- hash chains
- capsules
- stigmergic coordination traces
- indexed access to durable state

## Feed direction

```text
all modules
    -> BentAxis
    -> immutable traces / provenance / artifacts
```

BentAxis does not decide scientific truth.

It records what happened.

---

# 6. Colony — Population and Work Coordination

Colony is the execution population/scheduler layer.

Existing implementation includes `colony/scheduler.py`.

## Responsibilities

- schedule independent work
- manage worker population
- consume work descriptions
- emit results/traces
- coordinate through BentAxis

## Constitutional rule

Workers do not directly communicate with one another.

```text
Worker A -> BentAxis <- Worker B
```

not:

```text
Worker A <-> Worker B
```

## Feeds

Colony -> runtime execution jobs
Colony -> experiments
Colony -> replay jobs
Colony -> diagnostic jobs

## Receives

Work definitions from the experiment/runtime layer.

---

# 7. Evidence and Corpus Layer

This is a cross-cutting missing/under-specified piece that must be made explicit.

Every experiment must identify:

- corpus identity
- corpus hash
- information-set identity
- labels
- feature availability
- timestamp boundary
- source provenance
- preprocessing definition
- execution environment

## Canonical chain

```text
SOURCE
  -> CANONICAL CORPUS
  -> INFORMATION SET
  -> EXPERIMENT INPUT
```

Evidence is immutable once sealed.

Historical Layer1 and forward/reconstructed panels belong here, not inside TIAMAT itself.

---

# 8. Experiment Contract

Omega needs one canonical experiment object.

```text
Experiment
    hypothesis_id
    corpus_id
    information_set_id
    implementation_id
    metric_contract_id
    execution_manifest_id
    temporal_scope
    holdout_scope
```

Execution produces:

```text
ExperimentResult
    metrics
    predictions
    state traces
    diagnostics
    artifacts
    provenance
```

Every model family must use this contract.

This is the boundary that prevents custom wrappers from creating incomparable experiments.

---

# 9. Runtime Kernel

The runtime kernel is the deterministic execution substrate.

Existing pieces include:

- `runtime/events.py`
- `runtime/trajectory.py`
- `runtime/replay.py`
- `runtime/workers.py`
- `runtime/state_vector.py`
- `runtime/replay_registry.py`
- `runtime/constitutional_record.py`

## Responsibilities

- event ordering
- state progression
- trajectory recording
- replay
- worker isolation
- deterministic execution
- state-vector serialization
- replay registry
- constitutional runtime records

## Key invariant

```text
same evidence
+ same implementation
+ same configuration
+ same event order
= same result
```

If this does not hold, higher-level scientific comparisons are invalid.

---

# 10. Atlas / TESSERACT

Atlas is the topological navigation layer.

Existing pieces include:

- `atlas/interface.py`
- `atlas/hypercube.py`

TESSERACT is the conceptual topology/circuit model developed around Atlas.

## Responsibilities

Represent:

- nodes
- legal edges
- topology
- transition paths
- conductance
- resistance / impedance
- stored pressure / capacitance
- continuity / path momentum
- release gates

The TESSERACT_CIRCUIT concept belongs here.

## Feeds

Atlas -> structural context for runtime/TIAMAT.
Atlas -> legal transition space.
Atlas -> topology-aware analysis.

TIAMAT must not redefine the global topology itself.

---

# 11. Hypergraph

Hypergraph represents higher-order relationships that cannot be reduced safely to pairwise edges.

Existing implementation: `hypergraph/engine.py`.

Example:

```text
A ----+
B ----+---- R
C ----+
```

## Responsibilities

- multi-component relationships
- higher-order coupling
- interaction structures
- dependency groups

## Feeds

Hypergraph -> TIAMAT context
Hypergraph -> Oracle challenge structures
Hypergraph -> Sheaf compatibility structures
Hypergraph -> E.N.D. interaction hypotheses

---

# 12. Simplicial Complex

The simplicial layer provides geometric representation of higher-order relationships.

Existing implementation: `simplicial/complex.py`.

## Responsibilities

- simplices
- faces
- higher-order geometric structure
- structural neighborhoods
- topology-preserving decomposition

## Boundary with Hypergraph

Hypergraph answers:

> Which entities participate jointly in a relation?

Simplicial Complex answers:

> What geometric/topological structure does that higher-order relation induce?

They are complementary, not duplicates.

---

# 13. Sheaf — Local-to-Global Consistency

Existing implementation includes `sheaf/compat.py`.

Sheaf is the context-consistency layer.

## Responsibilities

- local observations
- overlapping contexts
- compatibility maps
- local-to-global consistency
- contradiction detection

Conceptual flow:

```text
local evidence A
local evidence B
local evidence C
       |
       v
   compatibility
       |
       v
 global state claim
```

## Feeds

Sheaf -> TIAMAT contextual state
Sheaf -> Oracle contradiction/challenge generation
Sheaf -> ERK evidence consistency
Sheaf -> E.N.D. unresolved contradiction classification

---

# 14. TIAMAT — Structural Dynamics Engine

TIAMAT is an important piece and remains canonical.

Existing runtime: `tiamat/engine.py`.

Existing reconciliation and interface documents define its boundary.

## Core identity

TIAMAT is a deterministic structural-dynamics detector, not a universal market predictor.

It reconstructs hidden state and transition behavior from observable information.

## Canonical runtime

Seven-mode state machine:

```text
Q -> P -> E -> C -> H -> R -> Rf
```

Primary reduced state:

```text
M3 = [B, V, D]
```

Optional temporal state:

```text
τ_D
τ_mode
```

Derived observables include:

- recovery
- pressure
- momentum
- residual load

The runtime uses explicit guards and a legal transition table.

The identification registry contains M0-M7, with M7/V6 retained as the permanent control.

## Historical dynamics to preserve as evidence

The recovered TIAMAT research included concepts such as:

- SimpleShock
- LiveDeficit
- RecoveryWeakness_v1
- hazard_raw
- hazard_score
- run age
- hinge
- residual damage
- latent hazard
- recovery capability
- coupled transfer pressure

These are not automatically equivalent to canonical runtime equations. They must be classified as:

- canonical runtime law
- derived observable
- identification feature
- historical hypothesis
- experimental feature

That classification is mandatory.

## Probability boundary

TIAMAT must not claim that an arbitrary score is a probability.

The probability interface is an explicit contract.

Historical implementations that fail the probability contract are recorded as **INCOMPARABLE**, not silently adapted to make them comparable.

---

# 15. TIAMAT State-to-System Dataflow

The canonical conceptual flow is:

```text
Evidence
   |
   v
Context / Sheaf
   |
   v
Structural representation
   |
   v
TIAMAT state
   |
   +--> excitation
   +--> damage
   +--> recovery
   +--> residual load
   +--> momentum
   +--> timers / hysteresis
   |
   v
Mode / guard evaluation
   |
   v
Structural forecast / diagnostic output
```

TIAMAT does not directly mutate hypotheses or decide final scientific survival.

---

# 16. ERK — Evidence / Risk Kernel

ERK exists as `erk/kernel.py` and `erk/runtime.py`.

ERK must remain distinct from TIAMAT.

## Responsibilities

- evidence/risk representation
- risk-state evaluation
- risk aggregation
- runtime risk consequences
- compatibility with historical evidence paths

## Boundary

TIAMAT:

> What structural state is the system in?

ERK:

> What evidence/risk consequence follows from that state under the defined contract?

This prevents TIAMAT from becoming the universal kernel.

---

# 17. Oracle — Adversarial Scientific Challenge

Existing implementation: `oracle/engine.py`.

Oracle is not another predictor competing for the same score.

Oracle asks:

> What would falsify this claim?

> Where is the hypothesis weakest?

> Which counterexample would be maximally informative?

## Feed direction

```text
TIAMAT / ERK / Court candidate
        |
        v
      Oracle
        |
        v
 challenge / counterexample
        |
        v
      Experiment
```

Oracle must remain outside the authority of the model it challenges.

---

# 18. Adversary

The historical Adversary concept should be recovered as an Oracle sublayer or explicitly separate module, depending on implementation evidence.

Its role is targeted hostile testing:

- counterexample generation
- boundary attack
- disagreement search
- failure-seeking experiment proposals

It does not decide the final winner.

---

# 19. UTV — Undertow / Turbulence / Vortex

UTV belongs on the adversarial/dynamic challenge side of the architecture.

Conceptually:

```text
Undertow
   -> emerging instability
Turbulence
   -> competing / interacting instability
Vortex
   -> self-reinforcing structural capture
```

UTV should not be reimplemented until its historical corpus/specification is recovered and reconciled with TIAMAT/Oracle.

Its first status should be **RECOVER / RECONCILE**, not invent-from-scratch.

---

# 20. Motif Engine

Motifs represent recurring structural patterns.

They should be derived from repeated evidence across independent cases, not invented merely because a model recognizes a pattern.

Conceptual flow:

```text
experiments
   -> trajectories
   -> recurring structures
   -> motif candidates
   -> cross-lineage validation
   -> accepted motif
```

Motifs feed Oracle and E.N.D., but do not become automatic rejection rules.

---

# 21. Hazard Kernel

The historical Hazard Kernel concept must be reconciled with:

- TIAMAT hazard state
- ERK risk state
- Oracle challenge state

Do not duplicate hazard equations.

First determine whether the canonical boundary is:

```text
Hazard Kernel
   -> TIAMAT structural hazard
```

or:

```text
TIAMAT -> ERK -> hazard consequence
```

The historical implementation/evidence decides this boundary.

Until reconciled, classify the Hazard Kernel as **ARCHITECTURE TO RECOVER**.

---

# 22. Hinge

Hinge is a transition-pressure / regime-change diagnostic concept.

Historical formula:

```text
hinge = 0.70 * tightness_z + 0.30 * age_z
```

Associated work includes age-stall behavior and transition pressure.

Hinge should initially be treated as a derived diagnostic, not as a new foundational subsystem.

Potential feed:

```text
TIAMAT state/history
   -> Hinge diagnostic
   -> Oracle / Court / research analysis
```

---

# 23. Court — Adjudication

Existing implementation: `court/engine.py`.

Court is the formal evaluator/adjudicator.

It consumes:

- ExperimentResult
- metric contract
- eligibility rules
- calibration/probability contract
- provenance
- holdout designation

It produces:

- PASS
- FAIL
- INCOMPARABLE
- ABSTAIN / UNRESOLVED where permitted by contract

## Court must not

- diagnose failures
- mutate hypotheses
- rewrite evidence
- inspect the final test spine during development

Failure is passed to E.N.D.

---

# 24. E.N.D. — Enhanced Failure Diagnosis

E.N.D. is the analytic failure layer.

Core principle:

```text
FAILURE = evidence
DIAGNOSIS = hypothesis
```

E.N.D. owns:

- immutable FailureRecord
- failure taxonomy
- diagnostic certainty
- competing explanations
- unresolved status
- interaction diagnosis
- causal-support classification

Certainty levels:

```text
UNKNOWN
CORRELATED
SUSPECTED
CONFIRMED
```

E.N.D. can say:

```text
UNRESOLVED
```

That is a successful diagnostic result when evidence is insufficient.

---

# 25. Darwin's Pond — Evolutionary Memory

Darwin's Pond is the generative reservoir, not the diagnostic engine.

It stores:

- failed hypotheses
- failure records
- lineage
- mutation history
- diagnosis references
- mutation budgets
- quarantine state
- resurrection history

Initial mutation vocabulary:

```text
SNIP
ALTER
HOLD
```

Merge/recombination remains deferred until the simpler loop is validated.

## Critical rule

Mutation is always a new hypothesis.

```text
M3
 |
 +--> M3-S1
 +--> M3-A1
```

M3 is never rewritten.

---

# 26. E.N.D. -> Pond Boundary

E.N.D. says:

> Why might this have failed?

Pond says:

> Given that diagnosis, what bounded descendant is worth testing?

Therefore:

```text
Court FAIL
   |
   v
E.N.D.
   |
   v
Diagnosis
   |
   v
MutationProposal
   |
   v
Darwin's Pond
   |
   v
New Hypothesis
   |
   v
L0 experiment
```

No silent feedback loop is permitted.

---

# 27. Test-Spine Firewall

This is a constitutional cross-cutting mechanism.

The final test spine must not be accessible to:

- E.N.D. diagnosis
- Darwin's Pond
- mutation generation
- Oracle adaptation
- Court tuning
- model selection tuning

The flow is:

```text
TRAIN
  |
  v
VALIDATION
  |
  v
E.N.D. / POND / ORACLE
  |
  v
LOCK
  |
  v
TEST
```

The test result is selection pressure, not training information.

---

# 28. Probability and Calibration Contract

Omega needs a universal probability contract.

A model must explicitly declare whether an output is:

- score
- ranking
- hazard score
- probability
- calibrated probability
- decision

A value in [0,1] is not automatically a probability.

## Historical TIAMAT consequence

Historical TIAMAT that cannot satisfy the probability preflight is passed to the diagnostic runner, recorded as:

```text
INCOMPARABLE
reason = probability_contract_failure
```

and execution continues for other candidates.

This preserves the historical evidence instead of adapting the interface to make the candidate appear comparable.

---

# 29. Replay and Conformance

Every canonical subsystem must support deterministic replay where applicable.

Replay must verify:

- same input identity
- same implementation identity
- same configuration
- same event sequence
- same state transitions
- same result hashes

BentAxis hash chains and runtime replay registry provide the infrastructure.

---

# 30. Canonical Data and Historical Research

Historical research must be preserved as evidence, not silently promoted into runtime law.

Important recovered artifacts include:

- 2020-2024 Layer1 historical spine
- 2025+ forward/proxy panel
- SimpleShock
- LiveDeficit
- RecoveryWeakness_v1
- hazard_raw / hazard_score
- episode/run-age machinery
- hinge / age-stall research
- TIAMAT identification registry
- M0-M7 family comparisons
- forward family scorecards

Each must have explicit status:

```text
CANONICAL_RUNTIME
DERIVED_OBSERVABLE
EXPERIMENTAL_FEATURE
HISTORICAL_HYPOTHESIS
RETIRED
INCOMPARABLE
```

---

# 31. Dataflow: Complete Scientific Loop

The mature Omega loop is:

```text
SOURCE
  |
  v
CANONICAL CORPUS
  |
  v
INFORMATION SET
  |
  v
HYPOTHESIS
  |
  v
EXPERIMENT CONTRACT
  |
  v
COLONY / RUNTIME
  |
  v
STRUCTURAL CONTEXT
  |
  +--> Atlas / TESSERACT
  +--> Hypergraph
  +--> Simplicial
  +--> Sheaf
  |
  v
TIAMAT / ERK / ORACLE
  |
  v
EXPERIMENT RESULT
  |
  v
COURT
  |
  +--------------------+
  |                    |
 PASS/ABSTAIN          FAIL
  |                    |
  v                    v
LINEAGE             E.N.D.
                       |
                       v
                 DARWIN'S POND
                       |
                       v
                BOUNDED MUTATION
                       |
                       v
                 NEW HYPOTHESIS
                       |
                       v
                      L0
```

---

# 32. Feed Matrix

| Module | Receives from | Feeds | Does not own |
|---|---|---|---|
| Constitution | governance | all modules | scientific results |
| Identity | canonical objects | all durable modules | model truth |
| BentAxis | all event/provenance producers | all consumers | inference |
| Colony | work definitions | runtime/experiments | scientific judgment |
| Corpus | source data | experiments | model selection |
| Information Set | corpus + availability rules | experiments | inference |
| Runtime | experiment + state definitions | trajectories/results | hypothesis mutation |
| Atlas/TESSERACT | structural definitions | context/TIAMAT | diagnosis |
| Hypergraph | relationships | context/oracle/END | final decisions |
| Simplicial | higher-order geometry | context/oracle | final decisions |
| Sheaf | local contexts | consistency/context | model selection |
| TIAMAT | context + evidence | structural state/diagnostics | final selection |
| ERK | evidence + state | risk/evidence assessment | structural state machine |
| Oracle | candidate claims/results | challenges/counterexamples | final authority |
| Adversary | Oracle targets | hostile experiments | selection |
| UTV | dynamic context | instability/challenge descriptors | authority |
| Motif | trajectories/failures | recurring structures | automatic rejection |
| Hazard Kernel | structural/risk evidence | hazard interpretation | duplicate hazard logic |
| Court | experiment results + contracts | PASS/FAIL/INCOMPARABLE | diagnosis/mutation |
| E.N.D. | failures + evidence | diagnosis | mutation execution |
| Darwin's Pond | diagnosis + failed hypotheses | bounded descendants | diagnosis |
| Replay | immutable experiment artifacts | verified result/state | mutation |
| Test Firewall | governance | access restrictions | scientific interpretation |

---

# 33. Authority Hierarchy

Authority is deliberately separated from inference.

```text
CONSTITUTION
    |
    v
GOVERNANCE / FIREWALL
    |
    v
COURT
    |
    v
AUTHORIZED OUTPUT
```

TIAMAT, Oracle, ERK, E.N.D., and Pond produce information.

They do not acquire authority merely because their output is sophisticated.

Principle:

> Prediction is not permission.

---

# 34. What Must Be Recovered Before New Implementation

The following historical concepts are present in the architecture but are not all represented cleanly in the current repository:

- Adversary
- UTV
- Motif Engine
- Hazard Kernel
- Hinge
- full Oracle challenge machinery
- richer TESSERACT/CIRCUIT semantics
- canonical corpus/data-generator lineage
- second-order overfitting controls

They must be recovered from historical artifacts before being recreated from memory.

The repository's current packages are the implementation baseline; historical documents, commits, PRs, archives, and experiment artifacts are evidence for reconciliation.

---

# 35. Implementation Status Model

Every subsystem should carry one of these states:

```text
CANONICAL
PARTIAL
RECOVER
RECONCILE
DEPRECATED
OBSOLETE
EXPERIMENTAL
```

No subsystem should be marked canonical solely because a directory exists.

---

# 36. Final Build Order

## Phase A — Foundation

1. Constitution
2. Identity / canonical bytes
3. BentAxis
4. Provenance / hash chain

## Phase B — Execution substrate

5. Corpus identity
6. Information-set contract
7. Experiment contract
8. Runtime event model
9. Deterministic replay
10. Colony scheduler/worker isolation

## Phase C — Structural representation

11. Atlas/TESSERACT
12. Hypergraph
13. Simplicial Complex
14. Sheaf

## Phase D — Scientific engines

15. TIAMAT
16. ERK
17. Oracle
18. Adversary
19. UTV
20. Motif Engine
21. Hazard Kernel
22. Hinge diagnostics

## Phase E — Adjudication

23. Probability contract
24. Calibration contract
25. Diagnostic runner
26. Court

## Phase F — Failure evolution

27. E.N.D.
28. Darwin's Pond
29. mutation budgets
30. quarantine
31. resurrection
32. cross-lineage failure patterns

## Phase G — Constitutional verification

33. Test-spine firewall
34. replay conformance
35. provenance verification
36. deterministic integration tests
37. holdout/regime/source robustness
38. authority firewall

## Phase H — Organism integration

39. Canonical Omega orchestrator
40. end-to-end replay
41. full corpus verification
42. final architecture freeze

---

# 37. What We Must NOT Do

Do not:

- create parallel TIAMAT wrappers
- adapt historical failures merely to make them comparable
- promote experimental equations to runtime facts without evidence
- let E.N.D. mutate hypotheses
- let Pond diagnose failures
- let Court diagnose failures
- let Oracle train against the test spine
- let failure genes become automatic blacklists
- add modules merely because they sound useful
- delete historical evidence because it is inconvenient
- preserve obsolete scaffolds for compatibility when they contradict canonical architecture
- allow multiple competing canonical implementations

---

# 38. Architectural Completion Criterion

Omega is not complete when every package imports.

Omega is complete when the following statement is demonstrably true:

```text
A canonical evidence set
        |
        v
is transformed into a canonical information set
        |
        v
is evaluated under an immutable hypothesis
        |
        v
through a deterministic experiment
        |
        v
producing reproducible evidence
        |
        v
challenged independently
        |
        v
adjudicated under an explicit contract
        |
        +--> survives -> retained lineage
        |
        +--> fails -> immutable E.N.D. diagnosis
                              |
                              v
                       bounded Pond proposal
                              |
                              v
                       new hypothesis identity
                              |
                              v
                             L0
```

with the final test spine remaining untouched until the system is locked.

---

# 39. Immediate Next Action

Before implementing more functionality, perform a repository-wide reconciliation against this document.

For every package/file/historical subsystem:

1. locate the current implementation;
2. locate historical implementations and PRs;
3. classify its status;
4. identify its inputs;
5. identify its outputs;
6. identify its authority;
7. identify its tests;
8. identify duplicate/obsolete implementations;
9. connect it to this dataflow;
10. only then modify code.

The goal is not to make Omega bigger.

The goal is to make **every historically important piece occupy exactly one correct architectural position**.

---

# 40. Architectural Principle

Omega's central invariant is:

> **Observe without rewriting history. Infer without confusing inference for evidence. Challenge without controlling the challenger. Evolve without mutating the past. Authorize only what has earned authority.**

That is the constitutional organism we are building.
