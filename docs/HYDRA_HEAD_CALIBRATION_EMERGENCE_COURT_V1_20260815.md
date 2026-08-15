# HYDRA Head Calibration + Emergence Court V1

Date: 2026-08-15

## Purpose

Build Hydra from independently earned information channels rather than assuming that the current compartment list or equations are correct.

Each candidate head is subjected to an add/remove search, then judged on multiple dimensions. A head survives only if its information recurs out of sample and is not merely a discovery-period artifact.

## Head jobs and primary objectives

| Head | Question | Primary objective |
|---|---|---|
| Hazard | Can this state rank impending danger? | ROC AUC + PR AUC + temporal stability |
| Burden | Does this state express useful probability magnitude? | Brier + calibration error + log loss |
| Recovery | Can this state separate failed vs successful outcomes and persist across time? | AUC + PR AUC + stability |
| Trajectory | Does direction/change identify transitions? | AUC + PR AUC + stability |
| Persistence | Does history add information beyond hazard? | incremental AUC + stability + probability quality |

AUC is treated as ranking/discrimination, while Brier is treated as a proper probabilistic score, not a pure calibration measure. Calibration MAE is therefore reported separately, together with log loss. This follows the standard distinction in forecast verification and scikit-learn's calibration guidance.

## Search procedure

1. Generate only causal transforms: lags, rolling summaries using prior observations, deltas, accelerations, and prior episode-tempo counters.
2. Divide 2020-2023 into discovery years.
3. Perform fold-safe candidate screening inside those years.
4. Run floating forward addition and backward removal separately for each head objective.
5. Apply a small complexity penalty so an extra feature must earn its place.
6. Freeze the resulting representation.
7. Evaluate once on untouched 2024.
8. Run permutation control on the frozen 2024 predictions.
9. Report year-by-year stability and worst-year performance.
10. Reject candidates that only look strong during discovery.

This structure follows the core leakage rule of nested feature selection: feature selection must remain inside the discovery/training process, because selecting on a holdout produces optimistic estimates. Consensus/stability-oriented nested CV is a useful precedent for treating recurrence of selected variables as a first-class result rather than merely maximizing accuracy.

## Forbidden predictors

The following cannot enter any head predictor matrix:

- `Crash72`
- `episode_type`
- `duration_bucket`
- `entry_path`
- `recovery_gate`
- `regime_30d`
- `hazard_bucket`
- timestamps / close values

These may be used only for cohort definition, post-hoc analysis, or target construction when explicitly authorized by the experiment.

## Required result record

Every head must retain:

- selected features and selection path
- 2024 ROC AUC
- 2024 PR AUC
- 2024 Brier
- 2024 log loss
- 2024 calibration MAE
- 2024 balanced accuracy
- discovery-year AUCs
- worst discovery-year AUC
- permutation null mean / 95th percentile / separation
- feature count

## Interpretation rules

AUC can establish that a state preserves ranking information without establishing that a probability has calibrated magnitude. Brier mixes reliability, resolution, and uncertainty, so Brier alone must not be used as a calibration verdict. A calibration curve / calibration error and log loss are therefore mandatory companions.

A high discovery score with weak 2024 performance is classified as an unstable historical pattern, not a discovered latent state.

A head that repeatedly contributes no independent information after conditioning on the other heads is a merger candidate. A head that consistently provides independent out-of-sample information is an architectural candidate. A newly discovered independent channel is allowed to create a sixth head.

## External methodological inspiration

- scikit-learn calibration documentation: probability calibration, Brier score and log loss distinctions.
- McKinney et al. (2020), *Consensus features nested cross-validation*: feature stability plus nested validation to control leakage and selection instability.
- Pudil et al. (1994), floating search methods for feature selection.

## Status

The executable court is committed as `experiments/hydra_head_emergence_court_v1.py`.

A 3,000-row smoke dataset covering 2020-2024 was used to validate execution and serialization. That smoke run is **not** treated as scientific evidence. The full canonical 43,848-row run must be performed from the supplied canonical CSV before any head is promoted.
