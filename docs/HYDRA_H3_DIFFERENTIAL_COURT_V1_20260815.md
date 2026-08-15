# Hydra H3 Differential Court V1 — 2026-08-15

## Purpose
Compare Hydra's H3 representation against the recovered TIAMAT H3 controller without allowing native `episode_type` or `duration_bucket` to enter Hydra inputs.

## Canonical basis
The H3 restart court uses the canonical `layer1_structured_hazard_arm_timeseries(15).csv`, 43,848 hourly rows, 2020-2024. It identifies 169 native `3_to_4` episode starts. The recovered H3 controller has a hard `hazard_score >= 0.966` trapped branch; below that boundary, recent episode tempo/history is more informative than current SimpleShock or recent hazard peak. fileciteturn105file0

## Hydra comparison protocol
For every eligible H3 start, capture:

- Hydra Hazard state
- Hydra Burden state
- Hydra Recovery state
- Hydra Trajectory state
- Hydra Persistence state
- Hydra H3 score/decision
- native TIAMAT H3 label (comparison target only)

Do not pass native `episode_type`, `duration_bucket`, or the native H3 label into Hydra.

## Disagreement taxonomy
1. hard-boundary agreement
2. hard-boundary disagreement
3. phasic/mixed agreement
4. phasic/mixed disagreement
5. temporal-context disagreement
6. recovery-context disagreement
7. unexplained residual

## Required ablations
A. Hazard only
B. Hazard + Burden
C. Hazard + Burden + Trajectory
D. Hazard + Burden + Trajectory + Persistence
E. Full Hydra state

For each model report accuracy, balanced accuracy, confusion matrix, and disagreement cases. Use leave-one-year-out evaluation where feasible.

## Guardrail
This court is a differential reconstruction experiment, not a claim that Hydra should reproduce TIAMAT exactly. A Hydra disagreement that improves OOS discrimination is evidence for an architectural enhancement, not an error by itself.

## Maximum-discrimination target
The strongest current hypothesis is that H3 requires a temporal/history state beyond instantaneous hazard, burden, or shock. The canonical restart court reports episode starts in the prior 24h AUC 0.6587 and prior 48h AUC 0.6722, while current SimpleShock is only 0.3872. fileciteturn105file0

## Status
Specification only. No result is claimed until an executable court produces it.
