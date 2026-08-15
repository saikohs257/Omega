# Hydra Recovery / Trajectory Rechallenge V1 — 2026-08-15

## Canonical data
43,848 hourly rows, 2020-2024, supplied canonical Layer-1 spine.

## Recovery conditional test
The previously observed Hazard + Burden 2024 calibrated baseline was:
- AUC 0.91221
- PR AUC 0.04182
- Brier 0.00785
- Log loss 0.04605

Adding `RecoveryWeakness_v1_lag6` produced:
- AUC 0.91952
- PR AUC 0.04592
- Brier 0.00780
- Log loss 0.04692

That is a +0.00731 AUC lift. The earlier 1,000-pair bootstrap on the frozen 2024 holdout gave a +0.0100 mean Recovery delta with 95% interval [+0.0060, +0.0144]. The result therefore remains supportive of Recovery as an independent information channel, but its calibration/log-loss behavior needs further work.

Recovery candidates tested: lag6, lag24, mean24, delta24, mean6, std24. Lag6 was the strongest AUC candidate; the full Recovery feature set did not improve on the single lag6 representation.

## Trajectory rechallenge
The current Trajectory representation was previously judged against Crash72. That was an invalid target for a direction/transition head, so a separate future transition target was created:

`future_3to4_24 = 1` when a native `3_to_4` episode start occurs in the next 24 hours.

2024 prevalence: 449 / 8,784 = 5.11%.

Single-candidate 2024 results:
- `hazard_score_mean6`: AUC 0.85266, PR AUC 0.24848, Brier 0.04099, LogLoss 0.15106
- `hazard_score_std24`: AUC 0.85710, PR AUC 0.18641, Brier 0.04603
- `SimpleShock_mean24`: AUC 0.83914, PR AUC 0.18773
- `SimpleShock_lag6`: AUC 0.71770
- `hazard_score_lag6`: AUC 0.80450

A conditional model using Hazard + Burden history + `hazard_score_mean6` reached AUC 0.86380 and PR AUC 0.27987. Adding `SimpleShock_mean24` did not improve AUC (0.84677) although PR AUC rose to 0.29122.

## Interpretation
1. **Recovery survives the conditional challenge provisionally.** It contributes information after Hazard + Burden, but the representation should be recalibrated.
2. **Trajectory is not dead.** Its earlier Crash72 rejection was target-mismatch evidence, not proof that directional state is useless. On an explicitly temporal next-state target, hazard history provides strong discrimination.
3. `hazard_score_mean6` is currently the strongest simple transition feature among the tested candidates.
4. Adding SimpleShock to the conditional transition model trades AUC for PR AUC. That is a real metric disagreement and should not be collapsed into a single score.
5. Persistence remains unproven as an independent head and should not be promoted yet.

## Next maximum-discrimination test
Build a dedicated transition-head emergence search using future 3_to_4 and other next-state targets, with AUC + PR AUC + Brier + log loss + temporal stability as the court. Keep Crash72 out of the Trajectory selection objective.

## Status
Empirical rechallenge result. No architectural promotion is final until the dedicated transition court is run walk-forward with a frozen 2024 holdout and permutation control.
