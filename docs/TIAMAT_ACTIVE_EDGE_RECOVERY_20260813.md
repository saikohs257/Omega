# TIAMAT Active-Edge Recovery — 2026-08-13

## Result

Recovered active/admission state machine reproduces the canonical 2020–2024 Layer-1 active mask exactly:

- active rows: 4,026 / 4,026
- active mismatches: 0
- starts: 453 / 453
- start mismatches: 0
- exits: 453 / 453
- exit mismatches: 0

This is materially better than the old level trigger `hazard_score >= 0.70`, which produced 116 active-row mismatches (16 FP, 100 FN).

## Recovered native-equivalent edge machine

Start edge:

```text
hazard_raw.diff() > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50
```

Exit edge:

```text
hazard_score.diff() <= -0.17
AND SimpleShock.shift(6) > 0.33
```

State update is stateful:

```text
if active and exit_edge:
    active = False
elif inactive and start_edge:
    active = True
```

This explains why activity can persist while instantaneous `hazard_score < 0.70`, and why an isolated `hazard_score >= 0.70` does not necessarily create an episode.

## Entry-path result

The recovered start mask plus previous-hour LiveDeficit quantizer matches native `entry_path` on 43,844 / 43,848 rows (99.9909%). One exception run remains:

```text
2021-05-04 02:00 through 2021-05-04 05:00
native entry_path = 2_to_4
prev-LiveDeficit quantizer = 3_to_4
```

At the start:

```text
2021-05-04 01:00 LiveDeficit = 0.920629
```

so the simple `>0.85 => 3_to_4` rule would predict `3_to_4`, while native history records `2_to_4`.

Therefore:

> `entry_path` is almost entirely a previous-LiveDeficit shell, but there is one documented historical exception and it must not be papered over with a universal rule.

## Upstream implication

The active/admission state machine itself is now highly constrained. The remaining upstream unknown is the exact native producer of `LiveDeficit` and its helper state.

Older archaeology also identifies the intended causal decomposition as:

- `RecoveryWeakness_v1` = failed healing / recovery failure
- `LiveDeficit_v1` = unresolved load
- `ReliefStall_v1` + `ExitCooldownScar_v1` = hysteresis geometry

One recovered historical expression for the relief stall is:

```text
dS_6h = SimpleShock[t] - SimpleShock[t-6]
dL_6h = LiveDeficit[t] - LiveDeficit[t-6]
ReliefStall_v1[t] = max(0, -dS_6h) * max(0, dL_6h)
```

This should be treated as recovered research evidence, not canonical runtime authority, until the native producer is replayed from raw OHLCV.

## Do not do

- Do not replace the recovered edge machine with the old `>=0.70` level trigger.
- Do not force the 2021-05-04 exception into the generic entry-path formula.
- Do not call `0.6*hazard + 0.4*LiveDeficit` canonical ActiveBurden.
- Do not claim the exact native LiveDeficit generator is recovered yet.
