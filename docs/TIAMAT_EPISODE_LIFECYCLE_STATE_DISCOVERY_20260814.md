# TIAMAT Episode Lifecycle State Discovery — 2026-08-14

## Forensic finding

The canonical 43,848-row Layer-1 panel contains 453 active episode runs. Within each native active run, `episode_type` is constant for the full run: all 453 runs have exactly one unique non-`none` type.

This does **not** mean the type must be decided from entry-only information. The native label is consistent with a state-machine output whose provisional classification can later be stabilized/reclassified by persistence.

## Native lifecycle separation

For `3_to_4` runs:

- `phasic`: 137 runs; duration 1–8h only.
- `mixed`: 25 runs; duration 9–23h.
- `trapped`: 7 runs; duration 26–99h.

There were no native H3 runs at 24–25h in the examined panel.

Three native `trapped` H3 runs start below the reconstructed hard entry boundary `hazard_score >= 0.966`:

- start hazard ≈ 0.964429, duration 35h
- start hazard ≈ 0.952574, duration 26h
- start hazard ≈ 0.952574, duration 31h

All three survive well beyond 8h. This strongly supports the interpretation that the recovered `hazard_score >= 0.966` rule is an **entry-time trapped branch**, while a provisional phasic state can later become trapped through persistence.

## Recovered tracker vs native target

Using the reconstructed Hinge tracker and recovered volume chain against the canonical hourly panel produced approximately 98.28% overall row agreement in this replay. The remaining errors are concentrated in the three topology-native heads rather than the active/admission edge machine.

This confirms the tracker is a strong reconstruction, but not canonical source authority.

## Critical methodological correction

Do not treat final `episode_type` as a pure entry-time target when recovering the causal H3 entry rule.

The correct conceptual decomposition is:

```text
observations
   ↓
entry/path router
   ↓
provisional episode state
   ↓
state persistence / reclassification
   ↓
final episode_type
```

The canonical active/admission machine is already exact given its upstream primitives:

```text
START:
Δhazard_raw > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50

EXIT:
Δhazard_score <= -0.17
AND SimpleShock[t-6] > 0.33
```

## What remains unresolved

1. Exact source-level generator for `episode_type` is not recovered.
2. The recovered Hinge tracker remains a reconstruction (~98% agreement), not canonical source.
3. H3 entry classification must be separated from persistence/reclassification when testing candidates.
4. `entry_path` is a separate router and should not be conflated with `episode_type`.

## Next discriminatory experiment

Recover the provisional H3 entry state independently, then replay the persistence transition rules. Score separately:

- entry-state agreement,
- persistence/reclassification agreement,
- final episode-type agreement,
- run-age agreement.

Do not tune a single aggregate classifier against final `episode_type`.
