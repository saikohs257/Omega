# Hydra Conditional Ablation Court V1 — Result

## Execution

Manual local execution against the canonical Layer-1 spine:
- 43,848 hourly rows
- 2020-2023 discovery/training window
- 2024 frozen holdout (8,784 rows)
- 169 native H3 starts verified
- Crash72 holdout positives: 67

The executable is `experiments/hydra_conditional_ablation_v1.py`.

## 2024 holdout — balanced-class logistic search model

| Nested model | AUC | PR-AUC | Brier | Log loss | Calibration MAE |
|---|---:|---:|---:|---:|---:|
| Hazard | 0.892886 | 0.042309 | 0.197257 | 0.596149 | 0.448583 |
| + Burden | 0.917983 | 0.044601 | 0.196676 | 0.590381 | 0.411778 |
| + Recovery | 0.917983 | 0.044601 | 0.196676 | 0.590381 | 0.411778 |
| + Persistence | 0.917983 | 0.044601 | 0.196676 | 0.590381 | 0.411778 |
| + Trajectory | 0.926621 | 0.046506 | 0.187403 | 0.572554 | 0.402720 |

Incremental 2024 changes:
- Hazard -> Burden: ΔAUC +0.025097; ΔPR-AUC +0.002292; Brier improves by 0.000581; log loss improves by 0.005768.
- Burden -> Recovery: zero change across every reported metric.
- Recovery -> Persistence: zero change across every reported metric.
- Persistence -> Trajectory: ΔAUC +0.008638; ΔPR-AUC +0.001904; Brier improves by 0.009273; log loss improves by 0.017827.

## Probability-quality check

Because class-weighted logistic regression changes the effective class prior, its raw probabilities are not a clean calibration experiment. A second unweighted probability-fit check was therefore run on the same frozen 2024 holdout:

| Model | AUC | PR-AUC | Brier | Log loss | Calibration MAE |
|---|---:|---:|---:|---:|---:|
| Hazard | 0.892886 | 0.042309 | 0.007834 | 0.046759 | 0.017247 |
| + Burden | 0.918156 | 0.044493 | 0.007817 | 0.045742 | 0.017427 |
| + Trajectory | 0.930529 | 0.048311 | 0.007942 | 0.045041 | 0.016667 |

The ranking conclusions survive the probability-specification check. Brier/log-loss must still be interpreted alongside calibration error; Brier is not a pure calibration measure.

## Permutation control

Final nested model (`Hazard + Burden + Trajectory`) on the frozen 2024 holdout:
- observed AUC: 0.926621
- shuffled-label mean AUC: 0.501575
- shuffled-label 95th percentile: 0.559339
- observed separation above null 95th percentile: 0.367283

## Critical target caveat

2023 contains zero Crash72 positives in this corpus, so no meaningful ROC-AUC exists for a 2023 Crash72 holdout. That year must not be fabricated into a stability score. The architectural conclusion here therefore rests on the 2024 frozen holdout plus the non-empty prior-year folds, with the 2023 target pathology explicitly recorded.

## Interpretation

1. **Burden earns its place.** Adding `LiveDeficit_lag6` after Hazard adds substantial out-of-sample information.
2. **Current Recovery does not earn a separate head.** Its current emergent representation is identical to Burden, and conditional ablation adds exactly zero information.
3. **Current Persistence does not earn a separate head.** Same result.
4. **Trajectory earns an independent channel.** Adding `SimpleShock_mean24` + `hazard_score_mean24` improves both discrimination and probability quality on the frozen holdout.
5. **Do not promote a final Hydra architecture yet.** Recovery/Persistence may be redundant, but this test cannot prove the concepts themselves are useless; it proves only that the current representations add nothing conditional on Burden.

## Methodological basis

The court uses a frozen holdout because feature selection/model selection on the test set creates optimistic bias; nested validation is the standard guard against that leakage. Floating search is used because it permits conditional addition and removal of features. Brier and log loss are treated as probabilistic scoring rules rather than calibration-only measures.
