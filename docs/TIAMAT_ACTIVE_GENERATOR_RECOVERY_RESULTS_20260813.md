# TIAMAT Active/Admission Generator Recovery Results

## Result

The recovered HF8 edge-triggered admission state machine reproduces the saved 43,848-row native active mask exactly.

### Recovered start edge

```text
hazard_raw.diff() > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50
```

### Recovered exit edge

```text
hazard_score.diff() <= -0.17
AND SimpleShock.shift(6) > 0.33
```

State update:

```text
if active and exit_edge:
    active = false
elif inactive and start_edge:
    active = true
```

## Native replay

- target active rows: 4,026
- recovered active rows: 4,026
- active mismatches: **0**
- start mismatches: **0**
- exit mismatches: **0**
- match rate: **1.000000**

The prior level trigger `hazard_score >= 0.70` produced 116 active-row mismatches (100 FN, 16 FP). The recovered edge state machine eliminates all of them.

## Entry-path result

The recovered bridge remains:

```text
prev LiveDeficit <= 0.70  -> 0_to_4
prev LiveDeficit <= 0.85  -> 2_to_4
otherwise                  -> 3_to_4
```

Against the native `entry_path` field:

- rows: 43,848
- matches: 43,844
- mismatches: **4**
- match rate: **0.999909**
- one mismatched run: 2021-05-04 02:00 through 05:00

On that run, native `entry_path = 2_to_4` while the simple previous-LiveDeficit quantizer predicts `3_to_4`.

## Interpretation

This is a major architectural recovery, but it is **not** the OHLCV-only primitive generator.

The admission state machine is now exactly reproduced **given the upstream primitives** `hazard_raw`, `hazard_score`, `LiveDeficit`, and `SimpleShock`.

The remaining unresolved question is upstream primitive generation—especially the canonical LiveDeficit producer and the single 2021-05-04 entry-path exception.

Do not promote a universal ActiveBurden scalar from this result. The evidence now supports a stateful edge-triggered admission machine with topology determined by prior LiveDeficit.
