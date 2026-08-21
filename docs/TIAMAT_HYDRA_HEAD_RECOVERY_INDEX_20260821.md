# TIAMAT / HYDRA Head Recovery Index

**Date:** 2026-08-21  
**Status:** ACTIVE RECOVERY INDEX  
**Purpose:** Prevent repeated archaeological reconstruction of already-recovered TIAMAT/HYDRA head work.

> This file is an index and preservation marker. It does not replace the source-backed handoffs, experiments, or court locks. Historical facts, current hypotheses, and unresolved lineage must remain distinct.

## Recovered canonical head map

TIAMAT is represented as a shared structural substrate with topology-native path heads and boundary/continuation timing seats.

| Head / seat | Native scope | Recovered role | Status |
|---|---|---|---|
| **H0 — FalseCalmIgnition** | `0_to_4` | spark / false-calm ignition / latent-fuel entry lane | recovered |
| **H2 — ResetDragRelease** | `2_to_4` | burden corridor / drag / stuck / reset-release lane | recovered |
| **H3 — RecoveryInversion** | `3_to_4` | recovery inversion / phantom-clear lane | recovered |
| **H4 — CeilingTrap** | `4_to_4` | critical self-loop / ceiling / no-escape proxy | scout-only until native aligned rows exist |
| **ExitBridgeDeficit** | episode boundary | exit bridge / next-trigger timing state | recovered |
| **PriorCarryDeficit** | shifted episode boundary | continuation-memory seat | recovered |

## Recovered mechanics

### H0 — FalseCalmIgnition

- Native path: `0_to_4`
- Entry-path gate, not a universal hazard predictor.
- Recovered behavior includes a high-hazard trapped boundary around `hazard_score >= 0.92`.
- Historical lane interpretation: shock-led / latent-fuel / spark.
- Recovered starter family: shock + false-calm fuel + range/volume expansion.
- Starter family is not canonical authority.

### H2 — ResetDragRelease

- Native path: `2_to_4`
- Burden/hazard entry gate.
- Recovered compound gate:

```text
(hazard_score >= 0.88 AND LiveDeficit >= 0.90)
OR
(hazard_score >= 0.95)
```

- Replaced an older shock-only trapped rule with inadequate recall.
- Historical interpretation: ActiveBurden + recovery failure + drawdown stress/scar.

### H3 — RecoveryInversion

- Native path: `3_to_4`
- Not a generic hazard classifier.
- Recovered hard trapped boundary around `hazard_score >= 0.966`.
- Native anchor recovered as approximately:

```text
LiveDeficit - SimpleShock_0_4h_max
AUC ~0.8929
```

- Historical interpretation: apparent recovery can occur while underlying burden remains unresolved.
- A later proxy BURDEN x HAZARD result did not survive native 43,848-row Layer-1 testing after final-label leakage removal; that proxy result is not native H3 authority.

### H4 — CeilingTrap

- Native path: `4_to_4`
- Critical self-loop / ceiling / no-escape condition.
- Native aligned `4_to_4` hourly rows were absent from the relevant panel.
- Critical-hazard self-loop proxy was therefore used.
- **SCOUT ONLY** until a native aligned extract is recovered.

### ExitBridgeDeficit

- Episode-end boundary state.
- Used for next-trigger / re-entry timing labels including 6h, 24h, and 48h horizons.
- Must be sampled at the episode-end boundary.
- Do not confuse with current runtime burden or shifted carry state.

### PriorCarryDeficit

- Shifted prior ExitBridge state.
- Represents continuation memory.

## Architecture interpretation

The safest recovered interpretation is:

```text
                         TIAMAT
                    shared substrate
                           |
             +-------------+-------------+
             |             |             |
            H0            H2            H3
         0_to_4        2_to_4        3_to_4
             |             |             |
             +-------------+-------------+
                           |
                          H4
                        4_to_4
                           |
                +----------+----------+
                |                     |
          ExitBridgeDeficit    PriorCarryDeficit
```

The heads are **not six independent canonical controllers**. Their meaning is scoped by topology/path location and shared structural substrate.

## Relationship to DIC / sidecars

Current working distinction:

- **DIC (Distributed Inference Collective):** historical collective name for the distributed inference sidecars/mechanisms. Do not assume a separate executable DIC subsystem without source evidence.
- **HYDRA heads:** internal TIAMAT head structure. Do not automatically equate HYDRA heads with DIC sidecars.
- **CHUG / Hinge / HF8 / HF9 / Seam / Attack / Release / Capacity / Exit Latch / BAGE / CARR:** sidecar/inference mechanisms whose exact mapping to individual HYDRA heads requires artifact-level recovery.
- **Oracle:** historically associated with fusion/synthesis; exact historical interface to DIC and TIAMAT remains subject to source recovery.
- **OMEGA:** later constitutional/runtime governance architecture; historical authority lineage must not be retroactively projected onto earlier Oracle/TIAMAT implementations.

## Anti-repetition rule

Before starting another memory reconstruction of these heads, inspect this index and the linked source-backed artifacts first.

### Primary source-backed documents already in this repository

- `docs/TIAMAT_RECOVERED_ARCHITECTURE_HANDOFF_20260813.md`
- `docs/TIAMAT_ENTRY_PATH_FORENSIC_RECOVERY_20260814.md`
- `docs/HYDRA_HEAD_EMERGENCE_COURT_AUDIT_20260815.md`
- `docs/HYDRA_HEAD_EMERGENCE_COURT_V2_LOCK_20260815.md`
- `docs/HYDRA_HEAD_CONDITIONAL_ABLATION_COURT_V2_LOCK_20260815.md`
- `docs/HYDRA_ARCHITECTURE_PROMOTION_GATE_V1_20260815.md`
- `experiments/hydra_conditional_ablation_v1.py`
- `experiments/results/TIAMAT_LANE_NATIVE_BATTERY_V1.md`
- `experiments/tiamat_native_route_extractor_v1.py`
- `tests/test_tiamat_native_route_extractor.py`

## Verification rule

This index does **not** promote scout/proxy findings to canonical authority. In particular:

1. H4 remains scout-only until native aligned `4_to_4` evidence is recovered.
2. Proxy H3 effects that failed native leakage-safe validation remain non-canonical.
3. DIC remains a collective terminology hypothesis unless an implementation proves a distinct DIC runtime layer.
4. Oracle fusion semantics remain source-recovery work unless the historical implementation establishes the exact fusion contract.
5. Historical implementation is not automatically current canonical implementation.

## Next archaeological target

Recover the exact mapping:

```text
DIC sidecar
    -> inference product
    -> Oracle fusion input
    -> HYDRA head (if any)
    -> TIAMAT state/guard
```

Do not reconstruct the same head tests from memory when the repository already contains the source-backed record.
