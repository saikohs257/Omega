# TIAMAT Native Lane Battery V1

## Fixed lane definition

Recovered entry-path producer:

```python
prev_ld = LiveDeficit.shift(1)

if prev_ld <= 0.70:
    entry_path = "0_to_4"
elif prev_ld <= 0.85:
    entry_path = "2_to_4"
else:
    entry_path = "3_to_4"
```

This experiment therefore treats the three lanes as fixed partitions of previous-hour LiveDeficit. No lane definition was fit from the target.

## Native data

43,848 hourly Layer-1 rows, 2020–2024.

## Models tested

- hazard
- burden
- H+B
- H+B+recovery
- H+B+shock+recovery

Targets:

- future active/episode presence at 1h, 6h, 24h
- Crash72

The first pass used in-lane logistic models to rank candidate projections. A separate leave-one-year-out pass tests whether the patterns persist OOS.

## In-sample lane results

### 0_to_4

- future 1h: H+B+shock+recovery AUC 0.941; hazard 0.891
- future 6h: H+B+shock+recovery 0.872
- future 24h: H+B+shock+recovery 0.814
- Crash72: H+B+recovery 0.645

### 2_to_4

- future 1h: H+B+shock+recovery 0.912
- future 6h: H+B+shock+recovery 0.842
- future 24h: H+B+shock+recovery 0.802
- Crash72: H+B+recovery 0.749; hazard alone 0.745

### 3_to_4

- future 1h: H+B+shock+recovery 0.970
- future 6h: H+B+shock+recovery 0.940
- future 24h: H+B+shock+recovery 0.863
- Crash72: hazard alone 0.712

## Leave-one-year-out results

### 0_to_4

6h mean AUC:

- H+B+shock+recovery: 0.872, minimum 0.836
- H+B+recovery: 0.861, minimum 0.825
- burden: 0.766
- H+B: 0.763
- hazard: 0.507

24h mean AUC:

- H+B+shock+recovery: 0.806, minimum 0.738
- H+B+recovery: 0.787, minimum 0.728
- H+B: 0.668
- burden: 0.657
- hazard: 0.558

Interpretation: 0_to_4 is the clearest recovery/complementary-information lane. Hazard alone is poor OOS for future persistence despite being the entry context separator.

### 2_to_4

6h mean AUC:

- H+B+shock+recovery: 0.832, minimum 0.784
- H+B+recovery: 0.820, minimum 0.756
- H+B: 0.695
- burden: 0.689
- hazard: 0.671

24h mean AUC:

- H+B+shock+recovery: 0.790, minimum 0.743
- H+B+recovery: 0.761, minimum 0.704
- hazard: 0.654
- H+B: 0.647
- burden: 0.603

Interpretation: 2_to_4 is a genuine multi-factor burden/recovery lane; the interaction needs context beyond one scalar.

### 3_to_4

6h mean AUC:

- H+B+shock+recovery: 0.935, minimum 0.906
- H+B+recovery: 0.934, minimum 0.905
- H+B: 0.923, minimum 0.898
- hazard: 0.904
- burden: 0.716

24h mean AUC:

- H+B: 0.853, minimum 0.806
- hazard: 0.850, minimum 0.806
- H+B+recovery: 0.850, minimum 0.816
- H+B+shock+recovery: 0.849, minimum 0.809
- burden: 0.683

Interpretation: 3_to_4 is the hazard-dominant lane. Adding burden/recovery helps at shorter horizons but adds little at 24h.

## Main finding

The lane-specific structure survives leave-one-year-out validation.

The three lanes do NOT share the same useful projection:

```text
0_to_4  -> recovery/complement-rich
2_to_4  -> burden + hazard + recovery
3_to_4  -> hazard-dominant, with short-horizon complements
```

Therefore a fixed universal ActiveBurden projection such as `0.6*hazard + 0.4*LiveDeficit` is not the most natural representation of the lane behavior.

## Important scope limitation

These results use causal fixed lane definitions but the future-active target is derived from the recorded future `entry_path`. This is valid for transition analysis but is not an independent reconstruction of the upstream `entry_path` generator itself.

No claim is made here that these coefficients are the original TIAMAT coefficients.

## Next experiment

Recover and test the **lane-native projection rules** themselves, then ask whether one shared latent substrate with lane-specific projections can reproduce:

- H0/H2/H3 semantics
- 8h phasic boundary
- ExitBridge timing
- PriorCarry
- fresh H4 gap survival

without using `episode_type` or future `entry_path` as predictors.
