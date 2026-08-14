# TIAMAT-Lite-1 Cross-Regime Ablation — 2026-08-14

Frozen transition gate:

```text
FULL       = Δhazard_raw > 1.00 AND LiveDeficit > 0.85 AND SimpleShock > 0.50
NO_SHOCK   = Δhazard_raw > 1.00 AND LiveDeficit > 0.85
NO_LD      = Δhazard_raw > 1.00 AND SimpleShock > 0.50
HAZARD     = Δhazard_raw > 1.00
```

Exit rule held fixed for all models.

## Results

| Model | 2020–2023 mismatches | 2020–2023 match | 2020–2024 mismatches | 2020–2024 match |
|---|---:|---:|---:|---:|
| FULL | 0 | 100.0000% | 0 | 100.0000% |
| NO_SHOCK | 3 | 99.9914% | 3 | 99.9932% |
| NO_LD | 12 | 99.9658% | 14 | 99.9681% |
| HAZARD ONLY | 15 | 99.9572% | 17 | 99.9612% |

## The three NO_SHOCK failures

They occur at:

- 2020-06-03 07:00 UTC
- 2020-06-03 08:00 UTC
- 2022-06-07 07:00 UTC

All are false positives from removing the SimpleShock gate. Their native rows have high hazard jump and high LiveDeficit, but SimpleShock remains below 0.50.

## Decision

Do **not** delete SimpleShock yet.

The evidence says it is almost redundant for admission: removing it loses only 3 rows out of 35,064 in 2020–2023 and 3 out of 43,848 overall. But it is still a real negative gate on those specific boundary cases.

LiveDeficit is more clearly indispensable: removing it creates 12 false positives in 2020–2023 and 14 over the full 2020–2024 spine.

Therefore the current minimum exact admission representation is still:

```text
Δhazard_raw > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50
```

For Lite simplification, the next experiment should target whether SimpleShock can be replaced by a cheaper derived state such as a shock/forcing bucket or whether the three exception rows share a single simpler condition.
