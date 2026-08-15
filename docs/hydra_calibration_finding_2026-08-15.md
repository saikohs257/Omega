# Hydra Calibration Finding — 2026-08-15

## Canonical state
- Dataset: canonical Layer-1 2020–2024 spine
- Rows: 43,848
- Columns: 15
- Native H3 starts: 169
- Frozen holdout: 2024
- Discovery: 2020–2023
- Calibration court CI: run #712
- Calibration commit: `de8fc5e467adff46f8a536d91840466295cee4bd`

## Finding
The raw Hydra logistic models show strong discrimination but badly mis-scaled probabilities on the 2024 holdout.

Representative raw vs calibrated behavior:

| Model | Raw AUC | Raw Brier | Platt AUC | Platt Brier |
|---|---:|---:|---:|---:|
| Hazard | 0.8929 | 0.1973 | 0.8929 | ~0.00779 |
| Hazard + Burden | 0.9180 | 0.1967 | 0.9180 | ~0.00778 |
| Hazard + Burden + Recovery | 0.9267 | 0.2099 | 0.9267 | ~0.00788 |
| Full Hydra | 0.9160 | 0.2067 | 0.9160 | ~0.00789 |

The raw model mean predictions were roughly 0.42 while the 2024 event prevalence was about 0.00763. Platt calibration reduced the probability-scale error dramatically while preserving AUC.

## Interpretation
1. The structural/ranking signal is strong.
2. Raw logistic probabilities are not trustworthy without calibration.
3. AUC and Brier measure distinct properties and must remain permanently co-reported.
4. Calibration does not by itself prove superior probabilistic forecasting versus the prevalence-only baseline; calibrated Brier/log-loss must still beat that baseline on repeated temporal folds.
5. Recovery can improve ranking while worsening raw probability quality; this is a real discrimination-vs-calibration tradeoff, not a contradiction.
6. The 2023 walk-forward fold has zero positive events; undefined AUC/PR-AUC must remain explicitly marked undefined rather than replaced with 0.5.

## Working hypothesis
Hydra should be treated as a measurement system for latent structural state, with separate stages for discrimination and probability calibration. The next scientific question is not "which head has the highest AUC?" but "which latent representation adds recurring information, and can that information be converted into calibrated probabilities that outperform a prevalence baseline?"

## Frozen rule
Do not alter the canonical data artifact, discovery/holdout split, or prior court outputs when testing follow-on calibration or latent-state hypotheses.
