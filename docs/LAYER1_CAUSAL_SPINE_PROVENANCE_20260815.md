# Layer-1 causal spine provenance — 2026-08-15

## Why the original 15-column panel is not a clean feature matrix

The recovered `layer1_structured_hazard_arm_timeseries(15).csv` is a mixed evidence panel. It contains runtime-style observables **and** hindsight/label fields in the same row. That is appropriate for forensic reconstruction and evaluation, but unsafe as an undifferentiated predictor matrix.

The uploaded source contains 43,848 rows and 15 columns. The source SHA-256 is:

`6f0dc516fdf3313ab27a38d942504d073faccba4067877531b44c219c5e4b31a`

The source includes `Crash72`, `entry_path`, `episode_age_h`, `duration_bucket`, and `episode_type`. Those fields must not enter causal feature discovery as ordinary predictors.

## Clean separation

### Causal feature spine

The canonicalizer keeps only:

- `open_time`
- `close`
- `SimpleShock`
- `LiveDeficit`
- `RecoveryWeakness_v1`
- `recovery_gate`
- `regime_30d`
- `hazard_raw`
- `hazard_score`
- `hazard_bucket`

### Future target

`Crash72` is a future outcome and belongs in the label sidecar, never in the feature matrix.

### Hindsight annotations

The following remain available for post-hoc evaluation, routing analysis, and native-controller comparison, but are not causal inputs:

- `entry_path`
- `episode_age_h`
- `duration_bucket`
- `episode_type`

## Structural validation

The canonicalizer requires:

- exactly 43,848 rows
- exactly 169 native `3_to_4` starts, defined as `entry_path == 3_to_4` and `episode_age_h == 1`

The resulting files are deliberately separate so an experiment cannot accidentally consume future labels as features.

## Important qualification

This is a **leakage-clean feature separation**, not a claim that every retained field has been independently proven causal. In particular, each retained state variable still needs temporal-lineage verification. The clean spine prevents obvious final-label/hindsight contamination; it does not magically establish causal validity.

The canonicalization implementation is `experiments/canonicalize_layer1_causal_spine.py`.
