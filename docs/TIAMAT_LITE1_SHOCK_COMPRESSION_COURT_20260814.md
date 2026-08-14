# TIAMAT-Lite-1 Shock Compression Court — 2026-08-14

## Four-step compression attack

### 1. Isolate the information carried by SimpleShock

Frozen full Lite-1 is:

`Δhazard_raw > 1.00 AND LiveDeficit > 0.85 AND SimpleShock > 0.50`

Removing SimpleShock creates exactly three false positives across the full 2020–2024 spine:

- 2020-06-03 07:00 UTC
- 2020-06-03 08:00 UTC
- 2022-06-07 07:00 UTC

The other two gates remain unchanged.

### 2. Check whether the failures are isolated accidental exceptions

They are not three unrelated singletons: two occur in consecutive hours on 2020-06-03. This argues that the SimpleShock gate is participating in a short-lived forcing boundary rather than encoding arbitrary row-specific noise.

### 3. Try the cheapest conceptual replacement

A general-purpose continuous SimpleShock model is unnecessary for the admission edge. The evidence only proves that TIAMAT consumes a single binary predicate:

`SimpleShock > 0.50`

Replacing it with another continuously valued shock model would not be simplification unless the replacement is demonstrably cheaper and preserves the same three vetoes. A hand-written exception list would be overfitting and is rejected.

### 4. Compression decision

For the admission subsystem, the minimum evidence-backed representation is still three binary predicates:

- hazard-jump gate
- structural-load gate
- shock/forcing gate

`SimpleShock` can be compressed from its full sensor computation to a single **forcing bit** at this boundary, but it cannot yet be deleted.

## Important limitation

The canonical 43,848-row CSV is not mounted in the current runtime, so no new numerical replacement test was performed in this pass. The three failure timestamps and cross-regime ablation numbers are taken from the already-saved canonical court in `TIAMAT_LITE1_CROSSREGIME_ABLATION_20260814.md`.

## Next decisive experiment

Recover the three veto rows' upstream fields and test whether a cheaper canonical forcing observable reproduces the exact same three vetoes. Do not add an exception table.
