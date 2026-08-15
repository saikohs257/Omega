# Hydra Architecture Promotion Gate V1 — 2026-08-15

## Purpose
Prevent exploratory AUC/Brier results from silently becoming architecture. A Hydra head may be promoted, merged, rebuilt, or rejected only after passing a head-specific target, provenance, temporal validation, calibration, and conditional-ablation gate.

## Evidence classes
- **Canonical:** supplied 43,848-row Layer-1 spine; native labels and documented recovered state definitions.
- **Exploratory:** Head Emergence Court V1 and related recorded rechallenges.
- **Admissible:** results produced by this gate with frozen methodology and reproducible executable code.

## Mandatory gates
### G1 — Observable provenance
Every predictor must be available at prediction time and traceable to observable substrate fields. Native TIAMAT hidden-state fields (`episode_type`, `entry_path`, `duration_bucket`, etc.) and derivatives are forbidden unless the experiment explicitly studies a native label post-hoc.

### G2 — Head-specific target
- Hazard: structural-state / active-hazard target, not Crash72 by default.
- Burden: severity/probability target appropriate to accumulated load.
- Recovery: recovery-failure / outcome target appropriate to unresolved damage.
- Trajectory: future transition target, e.g. future `3_to_4` within a fixed horizon.
- Persistence: incremental future-risk information conditional on Hazard + Burden.

### G3 — Temporal validation
Feature selection happens only inside the discovery period. For year Y, training uses years < Y. The final holdout is never inspected during search. A second outer test period is preferred for final promotion after repeated development.

### G4 — Probability integrity
Do not use class-balanced fitting when interpreting raw `predict_proba` as calibrated probabilities. Fit calibration inside training folds or use prior-preserving probabilistic estimation. Report Brier, log loss, and calibration error together.

### G5 — Multi-metric evidence
Every candidate reports ROC AUC, PR AUC, Brier, log loss, calibration error, and temporal stability. Metric disagreement is retained as evidence; no single scalar may erase it.

### G6 — Conditional increment
A head must add information after the heads already admitted. Report paired delta-AUC / delta-PR-AUC and probability deltas against the immediate predecessor model.

### G7 — Null control
Permutation control is required on the frozen holdout. The observed separation must materially exceed the permutation null.

### G8 — Complexity / stability
Prefer the smallest representation that recurs across forward folds and survives out-of-sample testing. A large discovery score with weak temporal transport is classified as an unstable historical pattern.

## Current empirical position
Recorded conditional evidence supports:
- Hazard: retain as a structural-state channel.
- Burden: retain; adds information beyond Hazard in the Crash72 court.
- Recovery: provisional independent channel; current `RecoveryWeakness_v1_lag6` adds ranking information beyond Hazard + Burden but needs probability/calibration work.
- Persistence: current representation is not independently demonstrated.
- Trajectory: current Crash72 representation is not a valid basis for rejection; a separate future-transition target is required. A recorded rechallenge found strong transition discrimination from hazard history, but its executable reproduction is not yet located.

## Promotion rule
No head is promoted to canonical Hydra architecture until G1-G8 are satisfied by an executable, reproducible court. Exploratory reports remain archived and must not be overwritten.
