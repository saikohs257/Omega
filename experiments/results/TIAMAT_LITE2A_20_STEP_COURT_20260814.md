# TIAMAT-Lite-2A — 20-Step Lane-Native Court

Date: 2026-08-14

## Canonical source used

`layer1_structured_hazard_arm_timeseries(15).csv`

43,848 hourly rows, 2020–2024.

Lane target follows the existing native lane battery: current row's fixed `entry_path` partition, with future target defined from future `entry_path != none` at 6h or 24h. This is transition analysis, not an independent reconstruction of the upstream entry-path generator.

Features:

- H = `hazard_score`
- B = `LiveDeficit`
- R = `1 - RecoveryWeakness_v1`
- S = `SimpleShock`

Each test uses leave-one-year-out logistic regression with training-fold median imputation and standardization. No target labels are used as predictors.

## 20 tests

### Steps 1–15: 6-hour LOYO AUC, five projections per lane

| Step | Lane | Model | Mean AUC | Min yearly AUC |
|---:|---|---|---:|---:|
| 1 | 0→4 | H | 0.6641 | 0.5065 |
| 2 | 0→4 | B | 0.7292 | 0.6596 |
| 3 | 0→4 | H+B | 0.7676 | 0.6436 |
| 4 | 0→4 | H+B+R | 0.7677 | 0.6507 |
| 5 | 0→4 | H+B+S+R | 0.7952 | 0.7074 |
| 6 | 2→4 | H | 0.7666 | 0.7252 |
| 7 | 2→4 | B | 0.8431 | 0.7712 |
| 8 | 2→4 | H+B | 0.8565 | 0.8050 |
| 9 | 2→4 | H+B+R | 0.8571 | 0.8009 |
| 10 | 2→4 | H+B+S+R | 0.8561 | 0.7972 |
| 11 | 3→4 | H | 0.7408 | 0.6753 |
| 12 | 3→4 | B | 0.8102 | 0.7240 |
| 13 | 3→4 | H+B | 0.8189 | 0.7389 |
| 14 | 3→4 | H+B+R | 0.8138 | 0.7388 |
| 15 | 3→4 | H+B+S+R | 0.8137 | 0.7370 |

### Steps 16–20: selected 24-hour LOYO AUC tests

| Step | Lane | Model | Mean AUC | Min yearly AUC |
|---:|---|---|---:|---:|
| 16 | 0→4 | H+B+R | 0.6157 | 0.4077 |
| 17 | 0→4 | H+B+S+R | 0.6465 | 0.4303 |
| 18 | 2→4 | H+B+R | 0.7421 | 0.6311 |
| 19 | 3→4 | H | 0.7412 | 0.5415 |
| 20 | 3→4 | H+B | 0.7513 | 0.6043 |

## What survives

### 0→4

The lane is not hazard-dominant. Burden is substantially stronger than hazard, and adding shock materially improves the 6h result. Recovery adds almost nothing on top of H+B in this reconstruction. Therefore the minimal practical projection is closer to `B + S`, with H as context, than the previously proposed H+B+R.

### 2→4

Burden is the strongest single axis; H+B is strong and stable. Recovery adds only about +0.0006 mean AUC at 6h and is not a clear necessity. Shock is not needed: H+B+S+R is slightly worse than H+B+R. The current simplest stable candidate is `H+B`.

### 3→4

This is NOT hazard-only on the measured future-active target. Burden is stronger than hazard, and H+B beats H alone at both 6h and 24h. Recovery and shock do not improve the 6h result and slightly reduce it. The simplest measured candidate is `H+B`.

## Critical methodological interpretation

These numbers do not prove the historical TIAMAT head formulas. They evaluate a forward reverse-engineering compression hypothesis against the recovered transition target under a fixed lane partition.

They also differ materially from earlier handoff summaries. That is useful: it indicates those earlier lane figures used different target construction or feature handling. The current court is therefore a **new executable measurement**, not a replacement for the older documented figures.

## 20-step verdict

The proposed Lite-2A specification:

```text
0→4 : H + B + R
2→4 : H + B + R
3→4 : H
```

is rejected as written.

The measured simpler structure is:

```text
0→4 : B + S   (H context)
2→4 : H + B
3→4 : H + B
```

But this is still not the final Lite architecture because the target is future-entry presence, not the final episode taxonomy. The next discriminator should be to test these minimal lane projections against native guard/episode outcomes while keeping causal timing strict.

## Next attack

Run the three reduced projections against:

1. native H0/H2/H3 branch outcomes where available,
2. 8-hour phasic/persistence behavior without using final `episode_type` as an input,
3. held-out 2025+ proxy data once the corresponding derived sensor spine is reconstructed.

Only add recovery, shock, or other mechanisms when an OOS failure specifically identifies the missing behavior.
