# TIAMAT A-axis Counterfactual Court V1

Status: research specification; no runtime authority.

## Purpose

Test whether the A-axis age router provides genuine conditional value rather than benefiting from pocket prevalence.

## Required row-level traces

For every eligible row retain:

- BASE_SPLIT_LAW
- HOT candidate
- PREC candidate
- selected mode
- fatal cell-fuse flag
- final ENTER
- final EXIT
- source legality
- target outcome
- B_age
- basin_id
- T3_CELL_ID_V21_1_CAUSAL
- chronological split
- year/regime/source/path identifiers when available

## Required comparisons

Compare selected routing against each counterfactual:

```text
selected route vs BASE
selected route vs HOT
selected route vs PREC
```

Evaluate globally, chronologically, by year/regime, and by routed pocket.

## Hard checks

- No train/test leakage in routing coordinates.
- No future episode-boundary feature in a prediction row.
- No threshold retuning after holdout inspection.
- No worse-both pocket may be hidden by aggregation.
- `shoot_through_guard == 0`.
- ENTER source legality preserved.
- EXIT source legality preserved.

## Interpretation

A global gain is insufficient. A routing mechanism is only interesting if the conditional choice explains why the selected head wins in the cells where it is selected, while remaining stable outside those cells.

A failure to beat counterfactuals is a useful result: it means B_age/cell routing may be descriptive rather than causal/predictive.
