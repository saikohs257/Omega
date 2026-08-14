# TIAMAT-Lite-1 Ablation Court — 2026-08-14

## Purpose

Determine whether the three inputs used by Lite-1 are all necessary, rather than assuming complexity is justified.

## Starting point

Lite-1 uses the recovered transition-pressure mechanism together with the canonical sensors:

- `hazard_raw` change / transition pressure
- `LiveDeficit`
- `SimpleShock`

The full transition gate previously reproduced the 2024 holdout exactly. This document records the next forensic question: which inputs are actually indispensable?

## Ablation protocol

Run the same frozen 2024 holdout under these nested models:

1. Full Lite-1: transition pressure + LiveDeficit + SimpleShock.
2. Remove LiveDeficit: transition pressure + SimpleShock.
3. Remove SimpleShock: transition pressure + LiveDeficit.
4. Remove both: transition pressure only.

No threshold retuning is permitted between ablations. The original Lite-1 thresholds remain frozen. This prevents the ablation from becoming another feature-selection exercise.

## Interpretation rules

- If an ablation preserves the exact holdout behavior, the removed variable is redundant for Lite-1 and should be deleted.
- If an ablation materially degrades behavior, the removed variable earns its place.
- If an ablation fails only on a narrow class, inspect that class before adding any new mechanism.

## Important provenance boundary

This is a behavioral distillation experiment, not a claim about the historical TIAMAT implementation. The canonical TIAMAT runtime itself remains a deterministic multi-mode state machine; its engine delegates state updates to `transition`, while the recovered scalar dynamics are explicitly documented as experimental/recovered evidence rather than silently promoted to the canonical machine.

## Current conclusion

The ablation results must be recorded numerically before simplifying the model. Do not infer redundancy from intuition. The next implementation step is therefore a frozen-threshold ablation replay on the canonical 43,848-row spine and the untouched 2024 holdout.
