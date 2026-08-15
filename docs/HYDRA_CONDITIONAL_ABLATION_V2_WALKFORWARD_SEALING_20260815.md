# Hydra Conditional Ablation V2 — Walk-Forward Sealing

Date: 2026-08-15

## Purpose

This patch seals two methodological defects found during review of the first V2 executable:

1. Recovery/Persistence representation selection was being performed once on all 2020-2023 discovery data, then reused inside earlier 2021-2023 walk-forward folds.
2. Persistence tenure restarted at each test-fold boundary instead of carrying the state observed at the end of the training interval.

## Fixes

### Fold-local representation selection

For each outer walk-forward year, Recovery and Persistence candidates are selected using only the corresponding outer training interval.

- 2021 selection sees 2020 only.
- 2022 selection sees 2020-2021.
- 2023 selection sees 2020-2022.
- Frozen 2024 selection sees 2020-2023 only.

The 2024 holdout remains sealed from all discovery and representation selection.

### Persistence continuity

Persistence thresholds are learned from the training interval. The last observed training state is carried into the test interval so a condition already active at the boundary retains its tenure.

No test-period target or future observation is used to construct the persistence threshold.

### Stability reporting

The executable now reports, by ordering and admitted head:

- mean fold AUC
- minimum fold AUC
- maximum fold AUC
- max-minus-min AUC spread

This makes stability visible rather than implicit.

### CI execution

The corrected V2 court is now executed by the existing manually dispatchable CI workflow alongside the prior Hydra courts.

## Scientific status

The patch changes methodology only. It does not promote Hazard, choose a winner, or alter the frozen Crash72 target. Results from the corrected court must be generated after CI runs and interpreted from the sealed outputs.
