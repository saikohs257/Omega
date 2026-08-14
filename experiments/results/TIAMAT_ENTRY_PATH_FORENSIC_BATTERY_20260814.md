# TIAMAT Entry-Path Forensic Battery — 2026-08-14

## Objective

Determine whether the native `entry_path` field is generated solely by previous `LiveDeficit` or whether the lone 2021-05-04 exception requires another immediately available state variable.

## Canonical baseline

```text
prev LiveDeficit <= 0.70  -> 0_to_4
prev LiveDeficit <= 0.85  -> 2_to_4
otherwise                  -> 3_to_4
```

Native comparison:

- 43,848 rows
- 43,844 matches
- 4 mismatches
- 99.9909% row match rate
- all four mismatches are one run: 2021-05-04 02:00–05:00

## Attack 1 — alternative LiveDeficit lags

Tested lags 1–12 hours.

Result: the one-hour previous-LiveDeficit rule is the dominant simple lag formulation. Longer lags substantially increase mismatches and therefore do not explain the native exception globally.

**Disposition:** reject wrong-lag explanation.

## Attack 2 — generic burden trajectory

Tested burden slopes/changes over short and longer windows.

Result: trajectory features can explain the exceptional local geometry but do not improve generalization enough to replace the simple previous-LiveDeficit router.

**Disposition:** hypothesis only; do not promote.

## Attack 3 — forcing/recovery trajectory

Tested combinations of recent SimpleShock movement and recovery movement.

Result: these produce plausible explanations for the exception but generate substantially more errors outside the exceptional run when used as general lane rules.

**Disposition:** reject as universal generator.

## Attack 4 — prior-shock/recovery override

Candidate:

```text
base = previous-LiveDeficit bucket
if base == 3_to_4 and prior SimpleShock > 0.50:
    route to 2_to_4
```

The exceptional 2021-05-04 run satisfies the candidate's prior-shock condition. However, the candidate has not been promoted because an exception-specific explanation is insufficient evidence of canonical provenance.

A `recovery_gate` qualifier is another candidate because the exceptional state carries recovery-state information not represented by the simple LD bucket.

**Disposition:** preserve as candidate; require full 453-start court.

## Forensic verdict

The evidence currently supports:

> `entry_path` is overwhelmingly a previous-LiveDeficit topology quantizer with one unresolved native exception.

The exception is not explained by merely changing the LD lag or by adding generic trajectory features.

The most promising remaining explanation is a **small state qualifier** attached to the high-LD (`3_to_4`) bucket, potentially involving prior forcing or recovery state.

The decisive next test is a leave-one-year-out comparison of:

```text
A: LD bucket
B: LD bucket + prior SimpleShock
C: LD bucket + recovery_gate
D: LD bucket + recovery state
E: LD bucket + forcing/recovery interaction
```

The winning rule must explain the 2021 run without creating new native mismatches.

## Evidence discipline

This battery deliberately does **not** use `episode_type` or `duration_bucket` as predictors. Those are downstream/final labels and would contaminate mechanism discovery.

The existing exact active/admission state machine remains untouched.
