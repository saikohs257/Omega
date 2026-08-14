# TIAMAT H3 Native Restart Court — 2026-08-14

## Ground truth

Native Layer-1 file:
`layer1_structured_hazard_arm_timeseries(15).csv`

43,848 hourly rows, 2020-2024.

H3 (`entry_path == 3_to_4`) starts: **169**

At start:
- `phasic`: 137
- non-phasic (`mixed`/`trapped`): 32

## Tests

### 1. Univariate discrimination of phasic vs non-phasic

AUCs at H3 entry:

- `tempo24`: **0.5952**
- `tempo48`: **0.5868**
- `RecoveryWeakness_v1`: **0.5209**
- `shock_prev`: **0.4122**
- `hazard_peak7`: **0.4116**
- `shock_max6`: **0.4102**
- `hazard_peak6`: **0.4009**
- `SimpleShock`: **0.3629**
- `LiveDeficit`: **0.3004**
- `hazard_score`: **0.2651**

The negative direction on hazard/LD is expected here: very high hazard/deficit is associated with the trapped branch rather than phasic.

### 2. Leave-one-year-out models

- hazard-only: mean AUC **0.7777**, minimum year **0.4000**
- hazard + recent tempo/history: mean AUC **0.7868**, minimum year **0.5043**
- shock-only: **0.6486**
- tempo-only: **0.5520**
- shock + tempo: **0.5457**

The best stable reconstruction tested was therefore **hazard history + tempo**, not raw LiveDeficit.

### 3. Tempo rule

For the causal pre-start count of prior H3 episode starts in the previous 24h:

- `tempo24 >= 1` with prior shock <= 0.70: precision **0.835**, 91 fires
- `tempo24 >= 2`: precision **0.950**, 40 fires
- `tempo24 >= 3`: precision **1.000**, 20 fires
- `tempo24 >= 4`: precision **1.000**, 11 fires

This supports the recovered tempo-override concept: clustered episode starts are highly enriched for phasic classification.

## Important constraint

The current 43,848-row Layer-1 CSV does **not** contain raw `volume`, so the exact recovered H3 tracker cannot be replayed verbatim from this file alone. The historical tracker uses a daily `volratio` input in addition to hazard history, shock, and tempo.

Therefore the native result above is a discrimination/reconstruction court, not a claim of exact tracker reproduction.

## Current forensic conclusion

H3 is best understood as a **two-branch controller**:

1. **Hard trapped branch:** `hazard_score >= 0.966`.
2. **Otherwise:** a phasic/acute score using recent shock, hazard history, recent volume expansion, and episode-start tempo; tempo can override the default.

The important result from the restart is that `LiveDeficit` is not the main discriminator of the H3 phasic/mixed split. The strongest native evidence points to **hazard trajectory + episode tempo**, with volume as an unresolved required input for exact replay.

Do not promote a simple residual-burden-only H3 formula as canonical.
