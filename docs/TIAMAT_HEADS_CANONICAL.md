# TIAMAT — Canonical Head Roles

## Purpose

This document preserves the recovered interpretation of TIAMAT's scoped heads so the project does not repeatedly lose the architecture during reconstruction.

**Important:** the heads are scoped by transition topology / lineage. They are not interchangeable generic predictors, and they must not be collapsed into one global score.

## Canonical head map

| Head | Scope | Role |
|---|---|---|
| **H0** | **0→4** | Handles the low-prior-burden entry lineage. It is the mechanism for admission from Stage 0 into Stage 4, not a generic “low hazard” predictor. |
| **H2** | **2→4** | Handles the intermediate-prior-burden entry lineage. It is the mechanism for the Stage 2 → Stage 4 transition. |
| **H3** | **3→4** | Handles the high-prior-burden / preloaded Stage 3 → Stage 4 boundary. This is a boundary mechanism, not simply the strongest version of another head. |
| **H4** | **4→4** | Handles persistence/release while already in Stage 4. It is concerned with continuation and release dynamics rather than fresh admission. |
| **ExitBridge** | exit/timing | Bridges the active state toward release. It is separate from the entry heads and should not be treated as another admission predictor. |
| **PriorCarry** | transition boundary / history | Carries prior-state information across the transition boundary so that the distinction between 0→4, 2→4, and 3→4 is preserved. |
| **T3** | baseline steering | Separate baseline-steering machinery; not one of the scoped entry heads. |
| **S2** | annotation / diagnostics | Diagnostic/annotation role only; not an authority head. |

## Why the heads must remain scoped

The historical system distinguishes transitions by **where the system came from** and by the state/history carried into the transition. Therefore:

```text
H0  != “low hazard predictor”
H2  != “another generic predictor”
H3  != “strongest predictor”
H4  != “another transition detector”
```

Instead:

```text
0→4  ──> H0
2→4  ──> H2
3→4  ──> H3
4→4  ──> H4
exit ──> ExitBridge
history ──> PriorCarry
```

This topology is part of the model semantics. Removing the scope changes the question each head is answering.

## Architectural placement

The recovered historical body constructs state and lineage first. The heads operate on that recovered body:

```text
historical observations
        ↓
primitive state
        ↓
stage / run state machine
        ↓
entry lineage + prior carry
        ↓
episode / temporal state
        ↓
        HEADS
   ┌────┼────┬────┐
   H0   H2   H3   H4
        │
   ExitBridge / PriorCarry
        ↓
authority firewall
```

## Provenance / guardrails

- This file records the project's recovered TIAMAT interpretation; it is not a claim that a missing original source file has been recreated byte-for-byte.
- The historical `LiveDeficit` generator remains a known archaeological gap. The historical Layer-1 witness values are available and should be used for replay rather than inventing a replacement generator.
- BVD/DVB are visualization/reference layers, not canonical state.
- Historical reconstruction code belongs in research/historical modules unless and until independently promoted through the project's authority gates.
- Do not merge head outputs into a single global “TIAMAT score” merely to simplify evaluation.

## Operational rule

When reconstructing or testing a head, always state its **legal transition seat**, its inputs, its output, and whether that output has authority or is diagnostic only. A head that works only after being given evidence from another head's seat has crossed the authority boundary and should be treated as a contamination/failure case.
