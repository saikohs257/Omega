# TIAMAT Entry-Path Forensic Recovery — 2026-08-14

## Status

**Purpose:** Preserve the latest forensic examination of `entry_path` so the reasoning is not lost between sessions.

### Important correction

A prior conversational conclusion stated that the `entry_path` generator had been completely solved by adding a prior-`SimpleShock` override to the previous-`LiveDeficit` bucket rule. That conclusion was **overstated** and is not currently canonical.

The repository's existing recovery result remains the governing evidence:

```text
prev LiveDeficit <= 0.70  -> 0_to_4
prev LiveDeficit <= 0.85  -> 2_to_4
otherwise                  -> 3_to_4
```

This reproduces 43,844/43,848 native rows, with one 4-hour mismatched run on 2021-05-04 02:00–05:00. See `docs/TIAMAT_ACTIVE_GENERATOR_RECOVERY_RESULTS_20260813.md`.

The exact source-level generator has therefore **not yet been proven**.

## What the new forensic work established

### 1. The simple previous-LiveDeficit quantizer is extraordinarily strong

Across the native 43,848-row Layer-1 panel:

- native rows: 43,848
- matches: 43,844
- mismatches: 4
- match rate: 0.999909
- all four mismatches belong to one continuous run:
  - 2021-05-04 02:00 through 05:00
- native path on that run: `2_to_4`
- simple quantizer prediction: `3_to_4`

This should be treated as **recovered approximation with one unresolved exception**, not as exact canonical source code.

### 2. Timing/trajectory models do not automatically improve the rule

Candidate explanations involving longer LiveDeficit lags, burden slopes, or generic forcing/recovery trajectories did not generalize as well as the one-hour previous-LiveDeficit quantizer.

Therefore the exception should not be explained by a complicated trajectory model merely because it is plausible.

### 3. The exception has a distinctive state

At the 2021-05-04 02:00 boundary, the prior state includes approximately:

```text
prev LiveDeficit  ~= 0.920629
prev SimpleShock  ~= 0.621818
```

The simple burden bucket therefore says `3_to_4`, while native says `2_to_4`.

The local state also shows declining recent forcing while burden remains elevated/rising. This makes a recovery/forcing qualifier a legitimate hypothesis, but **not a recovered fact**.

### 4. A prior-shock override is a candidate, not canonical authority

Candidate reconstruction tested:

```text
base =
    0_to_4 if prev LiveDeficit <= 0.70
    2_to_4 if prev LiveDeficit <= 0.85
    3_to_4 otherwise

if base == 3_to_4 and prev SimpleShock > 0.50:
    entry_path = 2_to_4
```

This candidate is attractive because the exceptional run has `prev SimpleShock > 0.50`, but it has **not been independently promoted by a full source/provenance court**.

Do not encode this candidate into runtime authority merely because it explains the exception.

## Architectural interpretation

The recovered architecture still supports treating `entry_path` as a **topology router** rather than a universal predictive feature.

```text
shared upstream state
        |
        +--> active/admission state machine
        |
        +--> entry-path topology router
                 |
          +------+------+------+
          |      |      |      |
         0_to_4 2_to_4 3_to_4 4_to_4
          |      |      |
         H0     H2     H3
```

The downstream heads must be interpreted inside their legal topology scopes. In particular:

- `0_to_4` = FalseCalmIgnition
- `2_to_4` = ResetDragRelease
- `3_to_4` = RecoveryInversion
- `4_to_4` = CeilingTrap proxy until native aligned rows exist

## Current forensic conclusion

**Solved:**

- `entry_path` is overwhelmingly determined by prior `LiveDeficit` buckets.
- The three principal lane thresholds are approximately 0.70 and 0.85.
- The four-row discrepancy is localized to one 2021 run.
- The path should remain a topology/scope variable, not a universal predictor.

**Not solved:**

- exact canonical generator source
- exact reason the 2021-05-04 run is `2_to_4`
- whether the exception is caused by `SimpleShock`, `recovery_gate`, another upstream primitive, or an unobserved state bit

## Next maximum-discrimination experiment

Test the 2021 exception against **all high-LiveDeficit starts** using only variables available immediately before the path decision.

Compare:

1. previous-LiveDeficit bucket only
2. bucket + previous SimpleShock
3. bucket + `recovery_gate`
4. bucket + recovery state
5. bucket + forcing/recovery interaction

Require:

- exact native lane reproduction
- no final-label leakage
- leave-one-year-out stability where sample size permits
- explicit accounting of every newly introduced mismatch

The winner is not the model that merely explains 2021-05-04; it is the simplest rule that reproduces the native lane assignments without creating new errors.

## Evidence boundary

The canonical active/admission reconstruction is already exact and should not be disturbed:

```text
start edge:
hazard_raw.diff() > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50

exit edge:
hazard_score.diff() <= -0.17
AND SimpleShock.shift(6) > 0.33
```

That reconstruction reproduces 4,026/4,026 active rows with zero start/exit mismatches.

This document concerns only the **remaining entry-path routing question** and must not be interpreted as evidence that the admission state machine itself regressed.
