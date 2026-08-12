# Omega First Poke

Purpose: observe the canonical machine without changing runtime behavior.

## Protocol

1. Run a baseline replay.
2. Apply one small deterministic perturbation to the input/evidence boundary.
3. Run the same replay again.
4. Compare BentAxis evidence, TESSERACT topology/state, TIAMAT mode/guards/timers, Court admissibility, and Oracle/Colony reactions.

## Rules

- No runtime tuning.
- No new equations.
- No Bitcoin-specific assumptions.
- No synthetic market data.
- Record the exact commit and input fingerprint.
- Preserve baseline and perturbed outputs separately.
- Do not interpret results until both traces are captured.

## Deliverable

Produce a machine-readable observation record showing the causal delta between baseline and one-poke runs.
