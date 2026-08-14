# TIAMAT LiveDeficit Ingredient Archaeology

## Status

Research checkpoint. This document separates recovered source facts from reconstruction hypotheses.

## Recovered exact primitives

- `ret_1h = log(close).diff()`.
- `ret_24h` is a 24-hour rolling sum of `ret_1h`.
- `ret_30d` is a 30-day hourly rolling sum of `ret_1h`.
- `realized_vol_24h = ret_1h.rolling(24, min_periods=24).std(ddof=0)`.
- `dd_30d = 1 - close / rolling(30d hourly maximum)`, with a 7-day warmup.

## Recovered shared-substrate ingredients from HF9/TIAMAT handoff

The archived design names:

- 72h drawdown stress
- 72h realized volatility stress
- 72h range stress
- quote-volume / volume stress
- shock persistence
- recovery failure
- hazard shelf / hazard persistence
- burden memory / hysteresis
- episode age
- regime context

No full-sample ranks, no future labels, and no raw `prev_*`/`prior_*` fields without proven timing lineage.

## Recovered revived-panel formulas (NOT asserted to be original TIAMAT)

The later revived panel builder constructs:

`Load_revived = 0.45 SimpleShock_rpr + 0.20 realized_vol_24h_rpr + 0.15 dd_30d_rpr + 0.10 iv_close_rpr + 0.10 ret_24h_rpr`

and:

`CSD_revived = 0.50 LiveDeficit_rpr + 0.20 recovery_absence_duration_h_rpr + 0.15 ld_ss_divergence_rpr + 0.10 episode_age_h_rpr + 0.05 dd_30d_rpr`

These are later revived constructs. They must not be silently promoted to the original LiveDeficit generator.

## Native-spine experiments

On the exact 43,848-row native Layer-1 spine:

- A revived proxy containing current LiveDeficit tracked native LiveDeficit at Pearson ≈ 0.834, Spearman ≈ 0.824, RMSE ≈ 0.144.
- CSD alone was Pearson ≈ 0.845, Spearman ≈ 0.853, RMSE ≈ 0.128, showing that the carried-damage component dominates this simple retrospective proxy largely because it contains current LiveDeficit.
- Removing current LiveDeficit lowered the full proxy to Pearson ≈ 0.717, so the revived recipe is not an independent reconstruction of the upstream body.
- Replacing current LiveDeficit with lagged LiveDeficit memory recovered Pearson ≈ 0.832, indicating that a causal memory channel may explain a substantial portion of the state trajectory.

These are diagnostic results only. They do not establish the original generator.

## Exact missing source symbols

The searched artifact corpus did not contain the original exact implementations for:

- `build_live_recovery_deficit()`
- `robust24h_downside`
- `robust_score()`
- `MarketShock`
- `StrainState`
- `StrainIndex`
- `RecoveryRatio`
- `RecoveryQuality`
- `StressInput`
- `RecoveryCredit`
- `PulseAcceleration`
- `BaselineElevation`
- `AsymmetricDrift`
- `cum_damage`
- `cum_healing`
- `raw_deficit`

## Important conclusion

The current evidence favors a stateful burden substrate with memory rather than a universal scalar ActiveBurden.

The next reconstruction target is the upstream LiveDeficit generator itself. The correct test is a true recursive replay seeded once, then driven only by causal market inputs and recovered helper definitions. A high correlation obtained by feeding native `LiveDeficit[t-1]` into the recurrence is not sufficient evidence of generator recovery.

## Next attack

1. Search exact archived source and historical transcripts for the ingredient primitives under alternate names.
2. Reconstruct 72h drawdown/volatility/range/volume stress definitions.
3. Reconstruct recovery-failure and hysteresis terms.
4. Determine whether lagged burden is the actual memory carrier.
5. Solve the missing forcing/helper term in the recovered LiveDeficit logit recurrence.
6. Run a full recursive 2020-2024 replay with no access to native LiveDeficit after initialization.
7. Use H2/H3/ExitBridge/entry_path as independent downstream courts.
