# TIAMAT H3 Exact Tracker Conformance — 2026-08-14

## Ground truth

`layer1_structured_hazard_arm_timeseries(15).csv`

## Source implementation

Recovered `thehinge_tracker.py` `gate_3to4()` and `run_tracker()` logic, using the recovered daily OHLCV artifact for `volratio`.

## Reproduction

The source tracker was replayed directly against the native 43,848-row Layer-1 spine.

Observed overall agreement:

```text
accuracy = 0.9802043423
mismatches = 868
```

This reproduces the documented ~98.02% result in the recovered tracker artifact.

## Native H3 branch composition

The native panel contains 169 `3_to_4` starts.

The recovered branch uses:

1. `hazard_score >= 0.966` -> `trapped`
2. otherwise compute phasic score from:
   - current SimpleShock
   - prior 6h hazard peak
   - five-day volume expansion derived from daily `volratio`
   - prior episode-start tempo over 24h / 48h
3. `score >= 1` -> `phasic`, else `mixed`
4. phasic episodes reclassify to trapped after age > 8h.

## Important forensic result

The daily volume chain is not the unresolved problem. The exact recovered tracker reproduces the previously documented ~98.02% overall fidelity when supplied with the recovered daily OHLCV-derived `volratio`.

Therefore the remaining 868 row mismatches are evidence about the reconstructed tracker/controller logic itself, not evidence that `volratio` was missing or incorrectly sourced.

## Mismatch structure

The direct replay produced these native-vs-predicted episode-type mismatches:

- native `mixed` -> predicted `trapped`: 411
- native `trapped` -> predicted `mixed`: 172
- native `mixed` -> predicted `phasic`: 112
- native `phasic` -> predicted `mixed`: 33
- native `trapped` -> predicted `phasic`: 24
- native `none` -> predicted `mixed`: 16
- native `phasic` -> predicted `none`: 16
- other mismatch rows: 94

This is not a single-threshold error. The dominant residuals are distributed across H2/H3/H0 and persistence/activation boundaries.

## Status

- Daily volume / `volratio` chain: **RECOVERED / CONFORMING TO SOURCE REPLAY**
- H3 hard trapped boundary `hazard_score >= 0.966`: **RECOVERED**
- H3 phasic/mixed scoring: **RECONSTRUCTED, NOT CANONICAL**
- Full episode tracker: **RECONSTRUCTED ~98.02%, not exact**

## Next attack

Do not tune the H3 thresholds globally.

Instead isolate the residual by branch:

- H2 entry gate residual
- H3 phasic/mixed residual
- H0 entry gate residual
- tracker persistence/episode-boundary residual

Then recover each branch against its legal native scope.

No reconstructed coefficient should be promoted to runtime authority without exact deterministic conformance.
