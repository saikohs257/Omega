# HF9 TIAMAT Runtime Rule Engine V2.1 — Handoff

## Status

Research/shadow runtime specification. Not runtime authority.

## Source

`hf9_tiamat_claude_fix_packet_20260613`

## Purpose

Promote the audited V2.1 control-logic correction without adding sensors or silently changing the Pathbook.

## Required changes from V2

| V2 action | V2.1 action | Policy |
|---|---|---|
| `RAISE_T3_STALE_DRAIN_WATCH` | `NO_STEER_T3_STALE_AMBIGUITY` | no directional drain steering after stale entry bias |
| `RAISE_T3_STALE_UPSHIFT_WATCH` | `RAISE_T3_STALE_UPSHIFT_SHADOW` | shadow only; insufficient independent run support |
| `ANNOTATE_S2_DRAIN_SCOUT_UNRELIABLE` | `NO_STEER_S2_DRAIN_CONTEXT_UNTRUSTED` | context annotation only |
| `RAISE_T3_AMBIGUITY_CONFLICT` | `RAISE_T3_AMBIGUITY_MODE` | ambiguity/instability state; never directional authority |

## Evidence carried forward

- stale T3 drain watch: 478 scorable rows, approximately 0.172 precision
- stale T3 upshift watch: 138 rows / 2 runs, approximately 0.978 precision
- S2 drain scout: 152 rows, approximately 0.020 precision
- T3 conflict: 598 rows / 16 runs, split 360 up / 238 drain

## Simulated V2.1 comparison

| version | scorable rows | scorable runs | row precision | run-normalized precision | median lead h |
|---|---:|---:|---:|---:|---:|
| V2 | 4621 | 450 | 0.763904 | 0.935815 | 35 |
| V2.1 | 3991 | 432 | 0.863192 | 0.970187 | 33 |

These are supplied simulation/replay results, not an independent canonical runtime result.

## Hard runtime boundaries

1. After 168h in State 3, stale entry bias cannot steer drain by itself.
2. Conflict is a separate ambiguity mode.
3. S2 drain remains context-only.
4. Stale upshift remains shadow until additional independent runs support it.
5. No future labels or forensic fields may enter legal-live output.
6. V2.1 does not grant probability or runtime authority.

## Next verification

Run V2.1 against the same frozen rows as V2 and compare action coverage, row/run precision, lead time, and age bands. Then run chronological and regime/source/path robustness splits before any promotion decision.
