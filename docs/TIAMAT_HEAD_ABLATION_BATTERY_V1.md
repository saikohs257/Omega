# TIAMAT Head Ablation Battery V1

**Status:** research-only evidence record. No runtime authority is promoted by this battery.

## Dataset

Canonical historical Layer-1 witness:

`layer1_structured_hazard_arm_timeseries.csv`

- 43,848 hourly rows
- 4,026 active rows
- 453 episode starts
- 63 H0 / 0→4 starts
- 221 H2 / 2→4 starts
- 169 H3 / 3→4 starts
- 3,573 H4 / 4→4 persistence rows

## Target

The controlled target used here is:

> survive the next 15 contiguous hourly observations while remaining active.

This is the **common structural target**, not the historical head-local target used by the separate historical full court. The two results must not be conflated.

## Candidate evidence

- LiveDeficit
- hazard_raw
- SimpleShock
- RecoveryWeakness_v1
- episode_age_h

The battery tests full evidence, leave-one-feature-out ablations, feature permutation, cross-head contamination, and leave-one-year-out generalization.

## Native-seat sensitivity

| Head | Full AUC | No LiveDeficit | No hazard_raw | No SimpleShock | No RecoveryWeakness | No age |
|---|---:|---:|---:|---:|---:|---:|
| H0 | 0.8775 | 0.8627 | 0.8301 | 0.8775 | 0.8742 | 0.8775 |
| H2 | 0.8882 | 0.8875 | 0.7415 | 0.8759 | 0.8879 | 0.8882 |
| H3 | 0.8228 | 0.8065 | 0.7465 | 0.8139 | 0.8282 | 0.8228 |
| H4 | 0.8638 | 0.8286 | 0.8428 | 0.8554 | 0.8568 | 0.8622 |

### What stands out

**H2:** hazard_raw is the largest single contributor in this common target. Removing it drops AUC from 0.8882 to 0.7415.

**H3:** hazard_raw is again the largest contributor. Removing it drops AUC from 0.8228 to 0.7465. LiveDeficit is secondary; shock contributes a smaller amount.

**H4:** both LiveDeficit and hazard_raw matter materially. Removing either produces a meaningful degradation. This supports H4 being structurally different from the entry seats.

**H0:** hazard_raw matters more than LiveDeficit under permutation, but the small H0 sample makes fine-grained ranking unstable.

**RecoveryWeakness_v1 and episode_age_h** contribute little incremental discrimination on this particular common target, especially for H0/H2/H3. That does not invalidate their historical semantic roles; it only says they are not strong incremental predictors for this target.

## Permutation sensitivity

Largest observed AUC losses after shuffling one feature while holding the fitted model fixed:

| Head | Feature | AUC loss |
|---|---|---:|
| H0 | hazard_raw | 0.1928 |
| H0 | LiveDeficit | 0.1438 |
| H2 | hazard_raw | 0.1940 |
| H3 | hazard_raw | 0.1622 |
| H3 | LiveDeficit | 0.0341 |
| H4 | LiveDeficit | 0.1177 |
| H4 | hazard_raw | 0.1153 |

Permutation is sensitivity evidence, **not causal proof**.

## Cross-head contamination

Training on one seat and testing on another did **not** cause all signal to disappear. Therefore the common structural target is not sufficient to establish strict mechanism uniqueness by itself.

The native-seat scores remained strongest or near-strongest for their own seats, while cross-seat models often retained substantial discrimination. This means:

> **head scope is supported structurally, but mechanism exclusivity is not yet proven by the common target.**

That is an important negative result. We should not oversell topology specificity from this battery alone.

## Leave-one-year-out

Selected ranges:

- H0: 0.7778–0.9000
- H2: 0.8147–0.9437
- H3: 0.6800–1.0000
- H4: 0.7638–0.9131

Interpretation:

- **H2** is the most stable entry seat in this experiment.
- **H0** is usable but sample-limited.
- **H3** is strongly regime/year sensitive despite strong within-court behavior.
- **H4** is broad and reasonably stable, with a noticeable 2023 degradation.

## Universal versus native models

A universal five-feature model versus separately fitted native-seat models produced:

- universal AUC: **0.8673**
- native combined AUC: **0.8710**
- improvement: **+0.0038 AUC**
- N: **4,026**

This is a **small** improvement and is not evidence by itself that a multi-head model is necessary.

## Classification

### PROVEN / REPRODUCED

- The historical topology gives distinct H0/H2/H3 entry seats and a large H4 persistence seat.
- The common-target battery is reproducible on the 43,848-row witness data.
- hazard_raw is a major incremental variable for H2 and H3 under this target.
- H4 depends materially on both LiveDeficit and hazard_raw.
- Leave-one-year-out behavior differs substantially by seat, with H3 the most regime-sensitive.

### PARTIAL

- Strict mechanism specificity of each head.
- Cross-head contamination resistance.
- Necessity of the multi-head architecture itself.

### UNRESOLVED

- The exact original internal equations/coefficients of each historical head.
- Whether the historical head-local targets can be reproduced from the 43,848-row witness alone.
- Causal necessity of any single feature.

## Guardrails

- Do not use BVD/DVB as canonical state.
- Do not reconstruct the missing native LiveDeficit generator from this evidence.
- Do not relabel structural scores as probabilities.
- Do not promote a head to runtime authority from this battery alone.
- Keep the historical local-head court separate from the common structural target.
