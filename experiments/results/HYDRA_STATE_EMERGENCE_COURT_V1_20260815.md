# HYDRA State Emergence Court V1 — 2026-08-15

## Objective
Discover a compact, stable state representation from the canonical Layer-1 time series by adding and subtracting candidate variables until the same structure repeatedly survives out-of-sample tests. The experiment deliberately does **not** assume Hydra's current Hazard/Burden/Recovery/Trajectory/Persistence decomposition.

## Method
The court combines ideas from sequential floating search and stability-oriented variable selection. Floating search allows features to be added and later removed, reducing the nesting problem of simple forward/backward selection. Stability is treated as a requirement rather than an afterthought: a discovery is not promoted unless it survives held-out time and permutation controls. urlFloating search methods (Pudil et al., 1994)https://doi.org/10.1016/0167-8655(94)90127-9

## Data guardrails
- Canonical spine: `layer1_structured_hazard_arm_timeseries(15).csv`
- 43,848 hourly rows
- H3 candidate rows: `entry_path == 3_to_4` and `episode_age_h == 1`
- 169 H3 starts
- Prediction target: `Crash72`
- Discovery period: 2020-2023
- Primary untouched holdout: 2024
- `entry_path`, `episode_type`, `duration_bucket`, `Crash72`, and `hazard_bucket` are not predictors.
- All generated history is causal: lags and trailing windows only.

## Search process
1. Generate causal candidate families from current signals: lag, trailing mean, and change at 1/3/6/12/24/48h where supported.
2. Add causal H3-history counters: H3 starts in the previous 24h and 48h, plus hours since prior H3 start.
3. Rank individual candidates on pooled 4-fold stratified discovery-period out-of-fold AUC/balanced accuracy.
4. Keep the top 12 candidates for the combinatorial stage.
5. Run forward floating addition with conditional backward removal.
6. Run backward floating removal from the same top-12 pool.
7. Evaluate both surviving subsets on untouched 2024 data.
8. Permute the discovery target 100 times as a null control.
9. Run walk-forward tests for 2021-2024 where the test year contains both classes.

## First run on the supplied 43,848-row spine
The initial emergence run produced a striking but **non-promotable** pattern:

### Discovery convergence
The strongest individual candidates were overwhelmingly **hazard history**, particularly:
- `hazard_raw_m48`
- `hazard_score_l6`
- `hazard_raw_l6`
- `hazard_score_m48`
- `hazard_score_l12`

Forward floating converged to:

```text
hazard_raw_m48 + hazard_raw_l6
```

with discovery-period pooled CV AUC about **0.922** and balanced accuracy about **0.835**.

Backward floating retained a four-variable hazard-history subset with discovery balanced accuracy about **0.892**.

### The critical falsification
On untouched 2024:

- forward subset AUC ≈ **0.452**
- backward subset AUC ≈ **0.557**

The forward subset also showed walk-forward AUC:
- 2021 ≈ 0.994
- 2022 ≈ 0.842
- 2023: not evaluable because the test year has no positive `Crash72` cases
- 2024 ≈ 0.452

The permutation control for the forward subset produced an observed discovery balanced accuracy of ≈ **0.835**, null mean ≈ **0.509**, with a 95th-percentile null around **0.709**. The discovery signal is therefore real relative to random labels, but it is **not temporally stable enough to call a recovered latent state**.

## Interpretation
This is exactly the behavior the emergence court was designed to reveal.

The search did **not** spontaneously discover a stable Hydra state. It discovered a powerful, highly specific **historical hazard pattern** that fails when the temporal regime changes into the untouched 2024 holdout.

Therefore:

> **Do not promote hazard history as a Hydra module merely because it wins the discovery search.**

The failure itself suggests the next experiment should search for representations that remain stable under regime change, not merely representations that maximize historical separation.

## Next-generation search
Add a stability objective directly to the selection criterion:

```text
emergence_score = mean(OOS_score)
               - instability_penalty
               - complexity_penalty
```

where instability measures dispersion across years/regimes and the complexity penalty increases with the number of retained variables and redundant correlated members.

Also test whether groups of correlated lag/rolling features represent one latent factor rather than separate heads. This follows the broader motivation for grouped/bilevel variable selection when predictors are correlated. urlInterpretability of bi-level variable selection methods (2024)https://doi.org/10.1002/bimj.202300063

## Status
**Court V1: PASS as a falsification instrument; FAIL as a state-discovery result.**

No new Hydra head should be promoted from this run.
