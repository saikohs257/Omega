# TIAMAT-Lite-0: Build & Falsification Court

Date: 2026-08-14

## Objective

Build the smallest plausible dynamical controller from the already-recovered causal primitives, then measure what it fails to reproduce before adding complexity.

## External inspiration

Sequential change detection provides a useful design precedent: CUSUM-style systems accumulate evidence over time rather than reacting to isolated observations, and their recursive/reset behavior is deliberately simple. CUSUM is widely used for sequential change detection; the recursion accumulates evidence and resets/floors after transient deviations. Sources: MathWorks CUSUM documentation and Ahad et al., Data-Adaptive Symmetric CUSUM. These are inspiration only, not evidence about TIAMAT's original implementation.

## Lite-0 design

Only three canonical primitive axes are used:

- excitation = `SimpleShock`
- burden = `LiveDeficit`
- recovery weakness = `RecoveryWeakness_v1`

No H0/H2/H3 heads, no volume features, no episode tempo, no duration rules, and no fitted multivariate model.

The controller is a two-threshold hysteretic state machine:

```text
enter ACTIVE when:
    excitation >= e_in
    AND burden >= b_in
    AND recovery_weakness >= r_in

remain ACTIVE until:
    excitation <= e_out
    AND burden <= b_out
    AND recovery_weakness <= r_out
```

Thresholds were selected only on 2020-2023 by a coarse random search over a compact parameter space. 2024 is a blind holdout for the test.

Best training parameters found:

```text
e_in = 0.798018
b_in = 0.852210
r_in = 0.151005

e_out = 0.323249
b_out = 0.396278
r_out = 0.086855
```

## Results

Canonical target: `entry_path != none`.

Lite-0:

```text
2020-2023:
  F1       = 0.1628
  precision= 0.1026
  recall   = 0.3944
  row match=0.6237

2024 holdout:
  F1       = 0.2298
  precision= 0.1659
  recall   = 0.3739
  row match=0.7795

All rows:
  F1       = 0.1720
  precision= 0.1103
  recall   = 0.3905
  row match=0.6549
```

For reference, the recovered canonical admission state machine reproduces the native active mask exactly when allowed to use the recovered upstream transition inputs (`hazard_raw.diff() > 1.00`, `LiveDeficit > .85`, `SimpleShock > .50`, with the recovered exit edge). Its native replay is 4,026/4,026 active rows, 453/453 starts, and 453/453 exits. That is a reference point, not part of Lite-0.

## Verdict

**LITE-0 FAILS.**

This is a productive falsification. The three primitive axes by themselves are not sufficient to reproduce the transition behavior. The failure is large, so adding cosmetic complexity would be pointless.

## What the failure tells us

The missing information is most likely one of:

1. transition/edge information (e.g. hazard acceleration or jump),
2. temporal accumulation/persistence, or
3. topology-specific routing.

The evidence from the recovered admission state machine strongly favors adding **one transition-pressure mechanism first**, because `hazard_raw.diff()` is a directly recovered edge signal and because CUSUM-style sequential methods also show why persistent/accumulated change can matter more than isolated level observations.

## Next experiment

Build **Lite-1** by adding exactly one mechanism to Lite-0:

```text
transition_pressure = hazard_raw.diff()
```

Do not add volume, tempo, episode labels, or head-specific logic yet.

The acceptance test remains the same 2024 blind holdout. If Lite-1 materially improves recall/F1 without exploding false positives, transition pressure is necessary. If not, kill it and test persistence/accumulation instead.

## Forensic rule

No feature gets added because it improves an in-sample metric. A new mechanism is admitted only when a specific Lite failure demonstrates that the information it carries is necessary.
