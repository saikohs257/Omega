# TIAMAT H3 Volume Source & Conformance — 2026-08-14

## Finding

The H3/Run-Tracker volume input is recoverable from the Hinge source chain.

Canonical source description:
- raw substrate: `btc_candles_5m_full.csv` (Binance perpetual 5m OHLCV)
- resample to daily OHLCV
- `volratio = daily_volume / rolling_30d_mean_daily_volume`
- 5-day expansion:
  `vr_exp = (vr_today - min(vr_last_5_days)) / min(vr_last_5_days)` when at least 3 valid days and positive minimum; otherwise fallback `0.5`.

The frozen Hinge specification reports the daily intermediates reproduce the saved panel exactly from the stated warmup period, including `volratio`.

## Native replay check

Using the supplied 43,848-row Layer-1 spine plus the recovered daily Hinge panel, the recovered H3 tracker logic replayed at 97.9634% overall agreement with native `episode_type`, 893 mismatched hourly rows.

This closely matches the documented reconstructed-tracker accuracy (~98.02%), so the result is consistent with the existing tracker artifact rather than a new independent canonical reconstruction.

## Interpretation

The volume chain is not the remaining blocker. The remaining discrepancies are in the reconstructed tracker/classifier itself, primarily the H2/H3 subtype decisions, not the daily `volratio` primitive.

## Evidence status

Strongly supported:
- daily OHLCV -> `volratio` formula
- 30-day mean definition
- 5-day expansion transformation
- use of volume expansion in H3 phasic scoring

Not yet proven canonical:
- the full reconstructed H3 classification logic
- exact native subtype decision boundaries beyond the hard trapped hazard boundary

## Next attack

Use the exact reconstructed H3 score as a falsification baseline, then inspect every native mismatch by branch:
1. hard trapped boundary (`hazard_score >= 0.966`)
2. phasic score contribution vector
3. tempo override
4. default mixed branch

The highest-value experiment is to identify which single reconstructed branch contributes the largest share of the 893 mismatches, then attack that branch only.
