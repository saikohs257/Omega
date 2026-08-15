# TIAMAT-Lite-1 Forcing Gate Re-evaluation — 2026-08-14

## Evidence basis

The canonical 2020-2024 hourly spine contains 43,848 rows. The recovered SimpleShock generator is independently documented and validated as exact against the Layer-1 reference: five inputs (`abs_ret`, `rv24`, `range_pct`, `log_qv`, `imb_abs`), 60-day rolling median/MAD normalization, sigmoid, then mean. See `strain_s1_walkforward.py` and the recovery handoff.

## Test

At the Lite-1 candidate boundary defined by the frozen transition-pressure gate:

`delta(hazard_raw) > 1.00 AND LiveDeficit > 0.85`

457 candidate rows occur in the 2020-2024 spine.

Applying the forcing bit `SimpleShock > 0.50` rejects only 2 of those 457 candidates:

- 2020-06-03 07:00 — SimpleShock 0.464986
- 2022-06-07 07:00 — SimpleShock 0.461630

Those two rows are the only candidate-level vetoes in this frozen gate. The nearby 2020-06-03 08:00 row has low SimpleShock as well, but it does not satisfy the delta-hazard > 1.00 condition and therefore is not a Lite-1 candidate.

## Forensic interpretation

The forcing signal is therefore a very small correction at this particular admission boundary, not a dominant component. The full SimpleShock composite remains important elsewhere in TIAMAT; this result does NOT establish that SimpleShock can be removed globally.

For Lite-1 admission, however, the minimum model can be tested as:

`delta(hazard_raw) > 1.00 AND LiveDeficit > 0.85`

with SimpleShock retained as an optional diagnostic/veto rather than a required latent state.

## Important qualification

This document deliberately does not claim 100% reproduction of `episode_type` or all active rows. The two-signal gate is an admission-candidate rule. It must not be conflated with the full TIAMAT episode detector, which includes its own state-machine and topology-specific logic.

## Decision

For the Lite simplification track, promote the two-signal version as `Lite-1A` and keep the SimpleShock-veto version as `Lite-1B` control. The next blind test should compare their downstream lifecycle behavior, not merely candidate-row counts.
