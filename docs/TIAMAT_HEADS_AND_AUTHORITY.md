# TIAMAT Heads and Authority — Recovered Working Semantics

**Status:** historical/research reference. Do not treat this document as a new inferred model.

This document preserves the head semantics recovered during the TIAMAT/Omega archaeology so they are not repeatedly lost between implementation passes.

## Core principle

TIAMAT heads are **scoped by transition topology / lineage**. They are not interchangeable generic predictors and should not be collapsed into one global score.

The historical body constructs state and transition context first. Heads then operate in their legal mechanism/timing seats. Visualization/diagnostic signals do not acquire authority merely because they correlate with an outcome.

## Recovered head roles

### H0 — 0→4 lineage

Handles the **0→4 entry lineage**: admission from the low-prior-burden state. It is scoped to that transition rather than being a generic low-hazard predictor.

### H2 — 2→4 lineage

Handles the **2→4 entry lineage**: admission from the intermediate-prior-burden state. Its identity comes from the transition topology and inherited prior state.

### H3 — 3→4 boundary

Handles the **3→4 boundary**: the high-prior-burden / preloaded entry condition. It is a boundary/mechanism head, not simply a stronger version of H0/H2.

### H4 — 4→4 persistence / release

Handles **4→4 persistence and release**: behavior while already in Stage 4, including persistence and the conditions surrounding release. It is not an entry head.

### ExitBridge

Separate **exit/timing machinery**. It bridges the active state toward release and should not be treated as another entry predictor.

### PriorCarry

Carries **previous-state/history information across the transition boundary**. It preserves the prior burden that makes the entry paths meaningfully different.

### T3

Separate **baseline-steering** machinery. It is not one of the scoped 0→4 / 2→4 / 3→4 / 4→4 entry/persistence heads.

### S2

**Annotation/diagnostic only.** It does not acquire authority merely from being useful for visualization or analysis.

## Authority rule

The legal flow is:

```text
historical observations
        ↓
primitive state/body
        ↓
stage + run + lineage
        ↓
scoped head
        ↓
timing / mechanism decision
        ↓
authority firewall
```

Do not reverse this by letting an aggregate hazard, visualization signal, or diagnostic sidecar silently become an owner/steering signal.

## Important distinction

- **BVD/DVB:** visual/reference layer; not canonical state.
- **Historical Layer-1 spine:** canonical witness data for replay.
- **Recovered body/state machine:** constructs stage, run, lineage, age, and related state.
- **Heads:** interrogate scoped transition mechanisms.
- **Sidecars/diagnostics:** may measure or explain behavior without owning it.
- **Authority firewall:** prevents diagnostic or out-of-seat evidence from becoming control authority.

## Provenance / confidence

The role definitions above are preserved from the prior TIAMAT/Omega working conclusions and historical project context. Where a role is not independently encoded in an executable artifact in the repository, this file records it as a **recovered working semantic**, not as proof of an exact original implementation.

The missing native LiveDeficit generator remains a separate archaeological gap. It is not required to preserve or replay the downstream head topology when the historical Layer-1 values are available.
