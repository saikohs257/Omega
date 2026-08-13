# TIAMAT Multi-Head Court — 2026-08-12

## Purpose

Research-only court for the historical HF9 TIAMAT formulation.

TIAMAT is evaluated as **scoped heads**, not as one universal scalar. This follows the historical doctrine: four topology-native heads plus ExitBridge and PriorCarry; no global promotion.

## Heads

- `0_to_4` → FalseCalmIgnition
- `2_to_4` → ResetDragRelease
- `3_to_4` → RecoveryInversion
- `4_to_4` → CeilingTrap
- `ExitBridgeDeficit` → episode-end next-trigger timing
- `PriorCarryDeficit` → mechanically shifted prior-episode continuation memory

## Historical timing rules

- ExitBridge is sampled at the exact episode end timestamp.
- PriorCarry is the previous episode's ExitBridge, shifted by episode order.
- First episode PriorCarry is null.
- No head is allowed to become a global resolver.

## Current implementation

The executable harness is:

`experiments/tiamat_multihead_court.py`

It fails closed when required historical fields are absent and reports each head in its native scope.

## Results from recovered historical substrate

A separate local replay on the recovered 43,848-row 2020–2024 hourly substrate produced the following exploratory results:

| Head | Rows | AUC |
|---|---:|---:|
| 0→4 FalseCalmIgnition | 63 | 0.8775 |
| 2→4 ResetDragRelease | 221 | 0.7340 |
| 3→4 RecoveryInversion | 169 | 0.6687 |
| 4→4 CeilingTrap | 3,573 | 0.8139 |

Timing heads:

| Target | ExitBridge | PriorCarry |
|---|---:|---:|
| next trigger 6h | 0.7835 | 0.5724 |
| next trigger 24h | 0.7363 | 0.5290 |
| next trigger 48h | 0.7129 | 0.5096 |

These AUCs are **fresh exploratory structural-comparison results**, not replacements for historical published CP15/chain metrics. No head is promoted by this report.

## BVD/DVB boundary

BVD/DVB remains a visual/reference projection. It is not promoted to historical canonical TIAMAT state by this experiment.
