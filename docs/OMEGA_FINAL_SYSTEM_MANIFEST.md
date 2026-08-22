# OMEGA Final System Manifest

**Status:** CANONICAL BASELINE UNDER CONSTRUCTION  
**Date:** 2026-08-22  
**Authority rule:** TIAMAT remains the behavioral baseline. No compression, successor, sidecar, predictor, or historical mechanism becomes canonical merely because it is simpler or scores well.

## 1. Canonical principle

The repository contains several generations of architecture. This manifest separates the working system from research and archaeology so historical material remains recoverable without silently becoming runtime authority.

**Golden behavioral reference:** `tiamat/`.

Any proposed replacement or compression must demonstrate behavioral conformance against TIAMAT before promotion.

## 2. Canonical runtime components

### OMEGA constitutional/runtime substrate
- Constitution / L0 invariants
- identity and event model
- evidence and experiment interfaces
- deterministic replay
- provenance / BentAxis

### TIAMAT
The primary deterministic structural-state engine and behavioral reference. It owns canonical structural state and legal state transitions.

### TESSERACT
A single architectural lineage for topology and legal-path representation. Historical `TESSERACT_CIRCUIT` naming refers to successive operational/circuit formulations of this lineage, not an independent sibling authority component.

### TESSERACT / CIRCUIT FORMULATION
The operationalized TESSERACT lineage includes the recovered Q4 board/topology work and later door, rail, path, trellis, calibration, and forensic generations. It does not independently authorize TIAMAT state transitions.

Strongly recovered topology laws include:
- Q4 has 16 nodes.
- Q4 has 32 undirected legal edges.
- A legal edge changes exactly one bit/axis (Hamming distance 1).
- A self-loop represents a hold condition.
- Multi-bit jumps are not silently treated as legal one-edge transitions.

Circuit vocabulary such as voltage/current, capacitance/inductance, quantum-walk scoring, or A*/beam search remains implementation-specific or experimental unless separately source-backed and replay-validated. These terms are not automatically L0 constitutional laws.

### HYDRA HEADS
Specialized TIAMAT-derived path mechanisms. These are distinct from HYDRA v0 architecture.

### ERK
Epistemic/risk evaluation layer. It does not own structural state.

### Oracle
The architectural fusion/proposal interface. The historical `oracle_fixed_bundle` establishes a concrete fusion lineage: multiple signal arms produce structured intermediate inference; trajectory/persistence and Self-Doubt evaluate those products; Triad combines Governor, Predictor, Adversary/Self-Doubt, and Braingut. The bundle's adversarial suite passes 11/11 in the recovered artifact.

The current OMEGA Oracle implementation remains a proposal/adjudication adapter. It is not silently replaced by the historical BTC-domain engine.

### Court
Core adjudication interface. Promotion/authority remains Court-gated. Current implementation is not assumed to represent complete historical Court semantics.

### BentAxis
Canonical provenance/replay/evidence substrate. It records evidence; it does not establish domain truth by itself.

## 3. DIC and evidence architecture

`DIC` is retained as the historical term for the distributed inference collective / sidecar family unless source recovery proves that a separate executable DIC engine existed.

The canonical design treats DIC as **distributed evidence production**, not as a controller:

```text
raw observations
      |
      +--> CHUG / Hinge / Seam / Attack / Release / Capacity
      +--> E/X / support / release / capacity variants
      +--> Exit Latch / BAGE / CARR / other specialized arms
      |
      +--> each emits bounded, observable evidence
      |
      +--> Oracle receives structured claims
```

A sidecar may disagree with another sidecar. Disagreement is retained as information and is not silently averaged away.

## 4. Oracle canonical enhancement

The canonical OMEGA Oracle direction is **evidence-preserving fusion**, not scalar prediction collapse.

A first-class `FusionObject` now exists in `oracle/fusion.py` with:

- source identity;
- target phase (`ENTER`, `EXIT`, `TRANSITION`, etc.);
- claim value;
- confidence;
- freshness;
- evidence dimensions;
- provenance;
- explicit agreement;
- explicit disagreement;
- missing channels;
- contradictions;
- replayable metadata.

The fusion primitive does **not** authorize a TIAMAT transition. It produces a structured inference object for ERK/TIAMAT evaluation.

### Oracle design rules

1. Do not collapse distributed evidence into one scalar merely for convenience.
2. Preserve minority evidence.
3. Preserve contradictory claims.
4. Preserve missing/stale channels.
5. Make uncertainty explainable.
6. Keep domain-specific historical Oracle logic as an adapter/reference rather than kernel law.
7. Never allow Oracle to self-promote authority.

### Historical Oracle lineage

The recovered `oracle_fixed_bundle` contains:

- Structural/Kinetic/Liquidity/Leverage/Narrative/Motif signal arms;
- state-vector estimation and consistency checking;
- trajectory and persistence layers;
- Self-Doubt;
- Triad;
- Governor;
- Predictor;
- Adversary/Self-Doubt;
- Braingut;
- calibration/replay material;
- adversarial tests.

Its historical exposure rule is retained as a **domain-specific reference invariant** rather than universal OMEGA law:

```text
final_exposure = min(governor_cap, predictor_desired) * adversary_haircut
```

The general OMEGA invariant derived from that pattern is stronger:

> Evidence may increase belief; evidence cannot grant authority.

## 5. ERK enhancement target

ERK should consume the full `FusionObject`, not merely a scalar Oracle score.

Minimum epistemic dimensions:

- calibration error;
- channel concentration;
- regime novelty;
- out-of-distribution status;
- stale evidence;
- sidecar disagreement;
- historical failure rate;
- provenance completeness;
- temporal causality.

`UNCERTAIN` is an explicit unresolved condition, **not equivalent to low risk or no signal**.

## 6. Sidecar contract

Every active sidecar should converge toward a common observable contract:

```text
SidecarEvidence {
    source
    target_phase
    observation / value
    confidence
    freshness
    evidence_dimensions
    bounded_state_metadata
    provenance
}
```

Allowed internal state is bounded and observable: finite windows, moving statistics, decay timers, hysteresis buffers, or equivalent explicitly replayable memory.

Forbidden:

- opaque state dependencies;
- independent structural-state mutation;
- irreversible authorization;
- hidden sidecar-to-sidecar mutation.

## 7. Phase specialization

The architecture preserves ENTER/EXIT asymmetry rather than forcing all mechanisms into a universal predictor.

Sidecars may explicitly specialize in:

- ENTER / excitation;
- EXIT / release;
- TRANSITION;
- RECOVERY;
- PRESSURE;
- STATE / persistence.

The recovered `exit_latch` result is an example of why this matters: strong EXIT specialization does not imply ENTER capability.

## 8. Counterfactual and adversarial test standard

Future sidecar/fusion tests should include:

- remove one channel;
- remove the majority channel;
- invert a channel;
- inject stale evidence;
- inject contradictory evidence;
- remove EXIT evidence;
- remove recovery evidence;
- change regime;
- replay identical evidence;
- verify deterministic output.

The objective is not merely F1. Measure:

- unique information;
- redundancy;
- complementarity;
- disagreement preservation;
- causal availability;
- replay stability;
- calibration;
- authority isolation.

## 9. Two HYDRAs — permanently distinct

### HYDRA v0 / HYDRA architecture
A TIAMAT-derived compression/compartmentalization experiment:

`Hazard + Burden + Recovery + Trajectory + Persistence -> Lane Coordinator`

It is **not** the primary runtime and is not presumed to perform as well as TIAMAT.

### HYDRA heads
The specialized path/head family recovered from TIAMAT:

- H0 FalseCalmIgnition
- H2 ResetDragRelease
- H3 RecoveryInversion
- H4 CeilingTrap
- ExitBridge
- Carry

These remain subject to their individual court/promotion status.

## 10. Research / shadow status

The following remain outside canonical runtime authority until they satisfy provenance, temporal-causality, deterministic replay, holdout, and promotion gates:

- HF8 authority claims;
- HF9 authority claims;
- retrospective HFLUX authority;
- unverified Hinge/HF8/HF9 equations;
- unresolved Seam laws;
- experimental CHUG variants as canonical state;
- speculative fusion laws;
- evolutionary mutation mechanisms;
- HYDRA v0 as a TIAMAT replacement.

## 11. Ownership invariant

Every active capability must eventually have exactly one canonical owner.

| Capability | Owner |
|---|---|
| Structural state | TIAMAT |
| Legal transition | TIAMAT |
| Topology / legal path representation | TESSERACT lineage |
| Circuit/path mechanics | TESSERACT lineage — operational formulation |
| Specialized path inference | HYDRA heads |
| Evidence production | DIC / sidecars |
| Evidence fusion | Oracle |
| Epistemic/risk evaluation | ERK |
| Promotion/adjudication | Court |
| Provenance/replay evidence | BentAxis |
| Constitutional invariants | OMEGA |

## 12. Canonical execution shape

```text
                    OMEGA CONSTITUTION
                           |
                     BENTAXIS / REPLAY
                           |
                    RAW OBSERVATIONS
                           |
                    DIC / SIDE-CARS
                     /            \
                    /              \
          TESSERACT               ORACLE
       topology/circuit       evidence-preserving
          lineage                 fusion
                    \              /
                     \            /
                          ERK
                    epistemic audit
                           |
                        TIAMAT
               canonical structural state
                           |
                     HYDRA HEADS
                   specialized paths
                           |
                         COURT
                           |
                        RUNTIME
```

TESSERACT constrains topology/path evidence. Oracle fuses evidence. ERK evaluates epistemic quality. TIAMAT owns structural state and transition. Court controls promotion. BentAxis preserves the provenance chain.

## 13. Finalization gate

This manifest becomes fully frozen only after the repository has:

1. enumerated actual executable entry paths;
2. verified TIAMAT replay behavior;
3. mapped every active sidecar to an owner/interface;
4. separated the two HYDRA meanings;
5. verified TESSERACT lineage and Circuit integration boundaries;
6. recovered and tested historical Oracle behavior;
7. integrated evidence-preserving fusion;
8. verified ERK/Court authority boundaries;
9. run integrated synthetic, adversarial, and historical differential tests;
10. produced a reproducible provenance ledger.

Until then, **CANONICAL BASELINE UNDER CONSTRUCTION** remains authoritative.
