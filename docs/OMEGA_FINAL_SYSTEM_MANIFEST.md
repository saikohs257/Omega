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

Strongly recovered topology laws include:
- Q4 has 16 nodes.
- Q4 has 32 undirected legal edges.
- A legal edge changes exactly one bit/axis (Hamming distance 1).
- A self-loop represents a hold condition.
- Multi-bit jumps are not silently treated as legal one-edge transitions.

Circuit vocabulary such as voltage/current, capacitance/inductance, quantum-walk scoring, or A*/beam search remains implementation-specific or experimental unless separately source-backed and replay-validated. These terms are not automatically L0 constitutional laws.

### TESSERACT topology/circuit evidence boundary
`TopologyWitness` may admit a circuit edge only when the edge is explicitly declared by the witness, is a legal Q4 one-axis transition, and the witness verifies as internally closed. The boundary is evidence-only: it does not infer missing edges, grant runtime authority, select TIAMAT transitions, or promote circuit semantics.

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

The canonical design treats DIC as **distributed evidence production**, not as a controller.

## 4. Oracle canonical enhancement
The canonical OMEGA Oracle direction is **evidence-preserving fusion**, not scalar prediction collapse.

A first-class `FusionObject` exists in `oracle/fusion.py` with source identity, target phase, claim value, confidence, freshness, evidence dimensions, provenance, explicit agreement/disagreement, missing channels, contradictions, and replayable metadata.

The fusion primitive does **not** authorize a TIAMAT transition. It produces a structured inference object for ERK/TIAMAT evaluation.

### Oracle design rules
1. Do not collapse distributed evidence into one scalar merely for convenience.
2. Preserve minority evidence.
3. Preserve contradictory claims.
4. Preserve missing/stale channels.
5. Make uncertainty explainable.
6. Keep domain-specific historical Oracle logic as an adapter/reference rather than kernel law.
7. Never allow Oracle to self-promote authority.

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

Sidecars may explicitly specialize in ENTER / excitation, EXIT / release, TRANSITION, RECOVERY, PRESSURE, and STATE / persistence.

## 8. Counterfactual and adversarial test standard
Future sidecar/fusion tests should include removal, inversion, stale evidence, contradictory evidence, regime change, identical replay, and deterministic-output checks.

The objective is not merely F1. Measure unique information, redundancy, complementarity, disagreement preservation, causal availability, replay stability, calibration, and authority isolation.

## 9. Two HYDRAs — permanently distinct
### HYDRA v0 / HYDRA architecture
A TIAMAT-derived compression/compartmentalization experiment. It is **not** the primary runtime and is not presumed to perform as well as TIAMAT.

### HYDRA heads
The specialized path/head family recovered from TIAMAT remains subject to individual court/promotion status.

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

The topology/circuit evidence boundary is now implemented and locally test-covered; it remains subject to the next CI run before being treated as an integrated verified path.

Until then, **CANONICAL BASELINE UNDER CONSTRUCTION** remains authoritative.
