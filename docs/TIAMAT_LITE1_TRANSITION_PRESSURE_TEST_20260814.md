# TIAMAT Lite-1 — Transition Pressure Test

## Purpose

Test the smallest evidence-backed extension of Lite-0: add the recovered transition-pressure signal `Δhazard_raw` to the three conceptual sensors `SimpleShock`, `LiveDeficit`, and `RecoveryWeakness_v1`.

## Important correction

The first scratch Lite-0 experiment used arbitrary thresholds and produced F1=0 on the 2024 holdout. That result is retained as a failed implementation attempt, not as a definitive statement about the three-sensor concept. The thresholds were not canonically grounded.

## Evidence-backed Lite-1 edge

The recovered canonical admission edge is:

```text
hazard_raw.diff() > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50
```

with exit:

```text
hazard_score.diff() <= -0.17
AND SimpleShock.shift(6) > 0.33
```

This is an evidence-backed behavioral reconstruction, not source-level primitive provenance.

## 2024 blind replay

Using the uploaded canonical 43,848-row Layer-1 spine and no fitting on 2024, the recovered edge replay produced:

- row match: **1.000000**
- precision: **1.000000**
- recall: **1.000000**
- F1: **1.000000**
- true positives: 773
- false positives: 0
- false negatives: 0

This exactly reproduces the native active mask on the 2024 holdout.

## Interpretation

Adding transition pressure is not merely a small feature improvement. It changes the Lite machine from a level-threshold detector into an edge-triggered state machine, which is the architectural behavior recovered from the canonical TIAMAT admission system.

The next simplification question is therefore not whether `Δhazard_raw` matters—it clearly does—but whether the three conceptual sensors can be reduced further while preserving the exact active-edge behavior.

## Next test

Hold the recovered transition-pressure edge fixed and remove one of the supporting gates at a time:

1. remove `LiveDeficit > 0.85`
2. remove `SimpleShock > 0.50`
3. remove both

Measure exact active-row/start/exit reproduction across all 43,848 rows and by held-out year. Add back only the minimum gate that is proven necessary.
