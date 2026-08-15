# HYDRA Head Conditional Ablation Court V2 — LOCK

Date: 2026-08-15

## Purpose
Determine which Hydra concepts carry independent information without allowing a native TIAMAT-derived state score to become an unquestioned conditioning anchor.

## Corrections from V1
V1 was rejected as an architectural authority because it:

1. allowed `hazard_score` to act as an unquestioned anchor despite its native-controller lineage;
2. used identical `LiveDeficit_lag6` representations for Burden, Recovery, and Persistence;
3. used one fixed head ordering;
4. mixed head-specific targets in one nested ablation;
5. did not pre-register stability and incremental decision rules.

## Target
The primary conditional ablation target is **Crash72 for every configuration**. This is a future outcome label and is not used as a predictor. Head-specific native-state targets are a separate court and must not be mixed into this ablation.

## Hazard audit
`hazard_score` is treated as **suspect native-state evidence**, not causal proof. Before it can anchor a Hydra configuration, report:

- 2024 holdout AUC/PR-AUC/Brier/log-loss against Crash72;
- discovery-period walk-forward metrics;
- worst-year and max-fold spread;
- permutation null;
- lineage flag stating that `hazard_score` is derived native TIAMAT state machinery;
- comparison with a clean hazard representation built only from runtime observables and their past-only transforms.

A near-perfect result is an investigation trigger, not a promotion.

## Representations
### Burden
Primary candidate: `LiveDeficit_lag6`.

### Recovery
Do not equate Recovery with Burden. Search candidates including:
- first difference of LiveDeficit;
- slope over 6h/24h windows;
- shock-adjusted residual `LiveDeficit - recent SimpleShock`;
- recovery weakness and its change.

### Persistence
Do not equate Persistence with Burden. Search candidates including:
- hours since LiveDeficit crossed a preregistered threshold;
- hours since recovery weakness crossed threshold;
- duration/tenure of the current burden state, using only past/current information.

The null result for current representations is explicitly **representation-conditional**, not concept-final.

## Walk-forward protocol
Discovery years: 2020–2023.
Frozen holdout: 2024.

For each walk-forward fold:
- fit transforms and probability models on training data only;
- apply to the next year only;
- never use 2024 for feature selection, threshold choice, calibration, or ordering choice;
- preserve chronological ordering.

## Stability
For each configuration report per-fold AUC and:

`auc_spread = max(fold_auc) - min(fold_auc)`

Also report mean AUC, median AUC, worst fold, mean PR-AUC, mean Brier, mean log-loss, and worst-fold Brier/log-loss.

A 0.01 mean-AUC improvement accompanied by materially larger instability must not be treated as an automatic promotion.

## Incremental decision rule
No post-hoc winner threshold is allowed. A candidate head is provisionally retained only when all are true:

1. mean walk-forward ΔAUC >= +0.01;
2. ΔAUC is positive in at least 3 of 4 evaluable folds;
3. frozen 2024 ΔAUC >= +0.005;
4. newest-head permutation shows observed incremental AUC above the 95th-percentile null;
5. Brier or log-loss does not materially deteriorate unless the head is explicitly classified as ranking-only;
6. complexity does not increase without incremental information.

These are promotion gates, not a single composite score.

## Ordering sensitivity
Run at least these three nested orderings:

1. Hazard → Burden → Recovery → Persistence → Trajectory
2. Hazard → Trajectory → Burden → Recovery → Persistence
3. Burden → Recovery → Trajectory → Persistence → Hazard

A head's decision is not final if its contribution exists only in one ordering. Report the range of incremental contributions across orderings.

## Newest-head permutation
For each nested addition, hold all previously admitted heads fixed and permute only the newly added head's representation within the evaluation fold. Compare:

`observed incremental AUC - 95th percentile newest-head null`

This isolates incremental information from joint-model performance.

## Coordinator architecture
The ablation court uses **separately fitted head outputs** inside each walk-forward fold. Raw features belonging to one head are not silently concatenated into another head's model. The coordinator may consume only frozen out-of-fold head outputs from the training period and then produce the held-out prediction.

## Decision vocabulary
- PROMOTE: independent evidence survives all gates.
- MERGE: concept adds no information after conditioning, across orderings, with adequate representation search.
- REWORK REPRESENTATION: current representation is redundant, but concept has an unresolved native role.
- REJECT: concept remains non-informative after representation search and controls.
- HOLD: evidence is ambiguous or the native target/lineage is not sufficiently clean.

## Non-negotiable leakage rules
Do not use as ordinary predictors:
- `Crash72`
- `episode_type`
- `duration_bucket`
- `entry_path`
- `episode_age_h`

`hazard_score` and `hazard_raw` remain flagged native-state-derived variables and must pass the hazard audit before being promoted as causal Hydra inputs.

## Required output
The executable court must emit:
- data lineage audit;
- target definition and counts;
- hazard audit;
- three ordering matrices;
- per-fold metrics;
- 2024 holdout metrics;
- newest-head permutation results;
- calibration/ECE results;
- complexity and feature counts;
- representation-conditional null findings;
- final PROMOTE/MERGE/REWORK/REJECT/HOLD status.

No Hydra architecture change is authorized from this court until the artifact is reviewed.
