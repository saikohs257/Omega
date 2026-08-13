# TIAMAT Head Semantics — Recovered Working Contract

**Status:** research / historical reconstruction

## Core principle

TIAMAT heads are **scoped by topology / transition lineage**. They are not interchangeable generic predictors and must not be collapsed into a single global score.

The recovered body constructs state and lineage first; the heads interrogate specific legal transitions or timing seats.

## Heads and roles

### H0 — 0→4 lineage
Handles the **0→4 entry lineage**: admission from the low-prior-burden path. H0 is a lineage/mechanism head, not a generic “low hazard” predictor.

### H2 — 2→4 lineage
Handles the **2→4 entry lineage**: admission from the intermediate-prior-burden path. H2 is a lineage/mechanism head, not merely another hazard predictor.

### H3 — 3→4 boundary
Handles the **3→4 boundary**: the high-prior-burden / preloaded entry condition. H3 is a strict boundary head, not simply the strongest/highest-risk head.

### H4 — 4→4 persistence / release
Handles **4→4 persistence/release**: what happens when the system is already in Stage 4 and remains there or transitions toward release. H4 is distinct from the entry heads.

### ExitBridge — exit / timing
Handles the **exit/timing seat**, bridging the current state toward release. It is not another entry head.

### PriorCarry — historical carry
Carries **previous-state / prior-burden information across the transition boundary**, preserving the history that makes the entry paths meaningfully different.

### T3 — baseline steering
Separate **baseline steering** machinery; it is not one of the scoped 0→4 / 2→4 / 3→4 / 4→4 entry/persistence heads.

### S2 — diagnostic / annotation
**Annotation / diagnostic only**. It is not an authority head.

## Authority rules

A head may only exercise authority in its defined transition/timing seat. Evidence belonging to another head, sidecar, visualization, or diagnostic layer must not silently become authority.

- Do not turn H0/H2/H3/H4 into a global ensemble score.
- Do not use H3 as generic risk ranking.
- Do not use H4 as an entry detector.
- Do not treat ExitBridge as an entry head.
- Do not promote S2 from diagnostic status.
- Do not allow sidecar/visual outputs to override canonical state.

## Recovered body → heads

```text
historical observations
        ↓
primitive state body
(SimpleShock / LiveDeficit / Recovery / hazard)
        ↓
stage FSM
        ↓
stage-4 run memory
        ↓
entry lineage + run age + cooldown
        ↓
episode / temporal state
        ↓
compression + age / Hinge
        ↓
scoped TIAMAT heads
        ↓
authority firewall
```

The historical Layer-1 witness panel contains the realized state/lineage outputs. The original native LiveDeficit generator is a known archaeological gap; it must not be silently replaced by a new generator and then called canonical.

## Provenance

This file preserves the recovered working semantics from the prior TIAMAT/Omega archaeology. It is a semantic contract, not a claim that every original implementation file survives. Where exact source evidence exists, tests and implementation should reproduce it; where the original implementation is missing, reconstructed behavior must remain explicitly labeled as reconstructed.

## Non-negotiable

**Do not forget the scopes.** Multiple heads being evaluated on the same historical panel does not make them one model. Their identity comes from the transition/topology seat they are allowed to occupy.
