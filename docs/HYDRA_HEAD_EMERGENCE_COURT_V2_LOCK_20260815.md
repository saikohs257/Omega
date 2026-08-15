# HYDRA Head Emergence Court V2 — Method Lock

Date: 2026-08-15

## Purpose
Produce admissible evidence for Hydra head existence, redundancy, or invention without importing reconstructed TIAMAT state or tuning against the final holdout.

## Method lock
1. Head targets are explicit and head-specific; Hazard is not scored universally against Crash72.
2. Candidate features must be observable at prediction time. No native `entry_path`, `episode_type`, `duration_bucket`, `episode_age_h`, or derivatives thereof may enter discovery unless explicitly designated observable for that experiment.
3. Every candidate receives provenance metadata: source column, lag/window, availability time, transformation, and target leakage status.
4. Probability fitting preserves the real event prior; any calibration stage is fit inside each training fold only.
5. Feature selection is nested inside an outer strict temporal evaluation loop.
6. For test year Y, training data contains only years < Y. No future-year observations enter training.
7. A final untouched test period is reserved and is not inspected for iterative tuning.
8. Head objectives and weights are frozen before the scientific run.
9. Conditional ablation is mandatory: Hazard → +Burden → +Recovery → +Persistence → +Trajectory, with incremental ROC AUC, PR AUC, Brier, log loss, and calibration metrics.
10. Permutation controls are run using the same selection pipeline.
11. Promotion requires incremental out-of-sample evidence plus temporal stability and null separation.
12. A head may be rejected, merged, or replaced; five surviving heads are never assumed.

## Required outputs
- provenance manifest
- selected feature sets per outer fold
- outer-fold predictions
- head metrics
- conditional deltas
- calibration curves / summaries
- permutation null summaries
- complexity counts
- final untouched-test result
- machine-readable JSON result

## Scientific disposition
V1 results remain exploratory only. No head promotion is authorized until V2 passes the method lock.
