# TIAMAT-Lite-2A — Lane-Native Minimal Model Specification

Date: 2026-08-14

## Purpose

Define the next falsifiable compression experiment from the recovered native-lane evidence. This is a forward reverse-engineering model, not a claim about canonical TIAMAT coefficients.

## Fixed scope

Use the recovered previous-hour LiveDeficit partition exactly as documented in the native lane battery:

- `0_to_4`: previous LiveDeficit <= 0.70
- `2_to_4`: 0.70 < previous LiveDeficit <= 0.85
- `3_to_4`: previous LiveDeficit > 0.85

No target-derived lane fitting. No `episode_type`, duration bucket, or future `entry_path` as predictors.

## Minimal lane projections to test

Start with the smallest evidence-supported projection per lane:

```text
0_to_4 -> H + B + R
2_to_4 -> H + B + R
3_to_4 -> H
```

where H = hazard, B = burden/LiveDeficit, R = recovery state.

This is intentionally simpler than the best in-sample model. The native battery shows that:

- 0_to_4 is recovery/complement-rich.
- 2_to_4 is genuinely multi-factor.
- 3_to_4 is hazard-dominant, with complements mainly at shorter horizons.

The native battery reports leave-one-year-out 6h AUC of 0.872 / 0.832 / 0.935 respectively for H+B+shock+recovery in the three lanes, while 3_to_4 reaches 0.904 with hazard alone. These are evidence for lane structure, not canonical coefficients.

## Compression rule

Do not add shock to a lane unless its omission causes a reproducible out-of-sample failure. Do not fit arbitrary coefficients merely to maximize in-sample agreement.

## Required tests

1. Evaluate each lane separately at 1h, 6h, 24h and Crash72 where labels are available without leakage.
2. Compare the minimal lane projection against the native battery's richer candidates.
3. Run leave-one-year-out validation.
4. Inspect failure cases by lane and horizon.

## Decision rule

A component earns a place only when its removal produces a material and repeatable OOS degradation in the behavior the Lite model is intended to preserve.

## Guardrail

The current evidence explicitly warns that the fixed universal projection `0.6*hazard + 0.4*LiveDeficit` is not the natural representation of lane behavior. Lite-2A therefore preserves lane-specific projections rather than forcing one scalar across all paths.

## Next question

After this lane-native test, determine whether one shared latent substrate can feed these three projections while retaining the observed lane differences. If yes, compress the implementation around that substrate. If no, retain three small lane projections.
