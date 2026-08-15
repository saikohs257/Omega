# Hydra Head Conditional Ablation Court V1 — 2026-08-15

## Purpose
Determine whether Burden, Recovery, and Persistence contain independent information after conditioning on the other candidate heads. Do not promote, merge, or delete a head from marginal AUC alone.

## Primary questions
1. Does Burden add information after Hazard?
2. Does Recovery add information after Hazard + Burden?
3. Does Persistence add information after Hazard + Burden + Recovery?
4. Does Trajectory add information after Hazard + Burden + Recovery + Persistence?
5. If a head does not add information, is the failure target-specific, representation-specific, or genuine redundancy?

## Metrics
For each nested model and head addition report:
- ROC AUC
- PR AUC
- Brier score
- log loss
- calibration error
- balanced accuracy
- fold-to-fold stability
- worst-year score
- permutation null separation
- parameter/feature complexity

Primary promotion criterion is incremental out-of-sample information, not marginal performance.

## Protocol
- Use the canonical 43,848-row 2020–2024 Layer-1 spine.
- Freeze the untouched 2024 holdout before selection.
- Perform discovery on 2020–2023 using walk-forward folds.
- Fit each probability calibrator only inside its training fold.
- Evaluate the frozen candidate on 2024 exactly once.
- Repeat with target permutations as a null control.
- Never use native `episode_type` as a Hydra input.

## Nested sequence
A = Hazard
B = Hazard + Burden
C = Hazard + Burden + Recovery
D = Hazard + Burden + Recovery + Persistence
E = Hazard + Burden + Recovery + Persistence + Trajectory

For every transition X→Y report delta AUC, delta PR-AUC, delta Brier, delta log loss and confidence interval/variation across walk-forward folds.

## Decision rules
- Promote a head only when its incremental signal survives the frozen holdout and permutation control.
- Merge a head when its contribution is statistically and operationally redundant with an existing head.
- Reject a head only after checking whether its target is mismatched or its representation is underpowered.
- If a head improves ranking but damages calibration, retain the representation only if calibration can be independently repaired without leakage.

## Current hypothesis
The first emergence court found Hazard strongly independent, while Burden/Recovery/Persistence repeatedly converged on `LiveDeficit_lag6`. Trajectory produced a distinct temporal representation. This court is designed to test whether that convergence reflects genuine redundancy or an inadequacy in the current Recovery/Persistence representations.

## Status
Specification locked. No architectural promotion is authorized until the executable court produces reproducible results.
