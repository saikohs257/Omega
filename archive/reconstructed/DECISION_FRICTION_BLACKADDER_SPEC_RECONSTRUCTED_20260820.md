# Decision Friction / Blackadder Spec — Reconstructed Deposit

Status: `RECONSTRUCTED_FROM_ARCHAEOLOGY`
Date deposited: 2026-08-20

This document preserves the implementation/audit facts recovered from prior work. It is not represented as byte-exact source.

## Recovered validation fixes

- `BlackadderInput.validate()` must range-check `spine_confidence` as `[0,1]` when supplied.
- Warm-up events used by the rolling baseline must have real variance; identical hardcoded warm-up rows are not a valid formula test.
- Example-row parity must be independent of rolling-baseline state.
- The immutable decision-record test must check every decision field, including `review_priority_flag` and `strip_to_spine_applicable_flag`.
- An explicit test must reject `spine_confidence=1.5` and `spine_confidence=-0.1`, while accepting `None`.

## Recovered conceptual fields

- `full_path_confidence`
- `spine_confidence`
- divergence magnitude
- divergence class
- `blackadder_score`
- `blackadder_mode`
- `effect`
- `haircut`
- `review_priority_score`
- `review_priority_flag`
- `strip_to_spine_applicable_flag`
- reason codes

## Recovered example-row parity

The implementation audit described an example row with approximately:

- magnitude: `0.548`
- mode: `ORNATE`
- effect: `proposed_reroute`
- haircut: `0.50`
- review-priority score: approximately `3.251`

Minor score differences from rounding order were within the stated tolerance.

## Open assumptions retained

- Outcome-flag direction depends on whether the metric is a failure metric or a positive metric.
- Reason-code emission threshold had been chosen as a first-pass `>0.5` sigma rule and required shadow-run auditing.

## Architectural interpretation

Blackadder is not a policy king. It is a deciding/audit mechanism constrained by constitutional scope. It measures decision friction between the full controller path and a simpler spine and uses that information to discount trust or raise review priority.

The correct interpretation of divergence is controller strain, not automatic predictive superiority.
