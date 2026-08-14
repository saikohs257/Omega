# TIAMAT LiveDeficit Nonlinear Drawdown Court — 2026-08-13

## Purpose

Test whether the canonical 43,848-row `LiveDeficit` can be explained by a price-only nonlinear drawdown state with persistence/relief, without using native `LiveDeficit` as an input.

## Native target

`layer1_structured_hazard_arm_timeseries.csv`, 43,848 hourly rows, 2020-01-01 through 2024-12-31.

## Candidate ingredients

- 24h drawdown
- 72h drawdown
- 168h drawdown
- 30d drawdown
- EMA-smoothed drawdown
- 6h/24h drawdown worsening and relief

## Results

Best simple nonlinear candidate:

```text
max_blend_sigmoid
```

constructed from 24h/72h/168h drawdown and a rolling standardized/sigmoid transform.

Results:

- Pearson r: **0.6318**
- Spearman rho: **0.5711**
- MAE: **0.1444**

A small causal basis ridge using drawdown levels, EMAs, worsening and relief terms reached:

- Pearson r: **0.5923**
- Spearman rho: **0.5635**
- MAE: **0.1516**

Therefore nonlinear drawdown alone does **not** reproduce native `LiveDeficit` closely enough to be considered the original generator.

## Interpretation

This is a falsification result, not a failure of the overall TIAMAT reconstruction. It rules out the simplest hypothesis:

> `LiveDeficit = nonlinear drawdown state + simple hysteresis`

The remaining generator likely contains additional state or forcing information, and the historical forensic report specifically identifies OI level/value stress as candidate ingredients. However, available historical OI in the local recon archive begins 2020-07-20 and lacks the full documented `sumOpenInterestValue` series for the complete 2020-2024 spine, so OI cannot yet be used for a complete cleanroom reconstruction.

## Important boundary

The exact historical `build_LiveDeficit()` implementation remains unrecovered. Do not promote any candidate above to canonical authority.

## Next attack

Recover the exact primitive/source lineage for:

1. OI level stress and OI value stress over the full 2020-2024 period.
2. Normalization/smoothing kernel.
3. Any stateful memory or recurrence applied after the stress blend.

The goal is a true recursive or deterministic replay that matches native `LiveDeficit`, not merely a high correlation to it.
