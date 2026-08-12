# TIAMAT D/V/B Visual Aide

## Status

**Diagnostic / visual aid only. Non-authoritative.**

D/V/B are **not historical TIAMAT variables**. They are a deliberately compact coordinate system used to visualize and compare state-like quantities in controlled experiments.

The historical TIAMAT evidence must always remain the source of truth for claims about what TIAMAT actually implemented.

## Purpose

The D/V/B aide is useful for asking intuitive questions such as:

- What happens when three state-like dimensions rise together?
- Does a combined representation carry more separation than one coordinate alone?
- Does temporal accumulation matter more than an instantaneous snapshot?
- Does an interaction term behave differently from its individual components?

It is a **map**, not the territory.

## Naming discipline

Use these labels in reports and figures:

- `D` — diagnostic coordinate
- `V` — diagnostic coordinate
- `B` — diagnostic coordinate
- `DVB` — combined diagnostic magnitude
- `DVB_history` — fixed-window accumulated diagnostic representation

Never describe these as "original TIAMAT variables" unless an authoritative historical artifact explicitly establishes that fact.

## Separation from historical TIAMAT

```text
Historical TIAMAT
    |
    +-- observed replay variables
    +-- actual runtime behavior
    +-- historical guards / modes / transitions
    |
    +--> evidence base

D/V/B Visual Aide
    |
    +-- reduced coordinate system
    +-- controlled synthetic trajectories
    +-- diagnostic comparisons
    |
    +--> hypothesis generation / visualization
```

The visual aide may suggest a hypothesis about historical TIAMAT. It may not rewrite the historical record.

## Existing implementation

The executable diagnostic harness is:

`tiamat/dvb_benchmark.py`

Its module docstring explicitly defines the benchmark as non-authoritative and diagnostic. It consumes canonical `TiamatState` objects for the controlled benchmark, but the existence of a `TiamatState` adapter must not be interpreted as proof that D/V/B were historical TIAMAT fields.

The current CI regression suite validates the benchmark independently from the historical replay analysis.

## Scientific rule

When reporting a result, distinguish:

**Historical result**

> "The historical replay contains X and X predicts Y."

from:

**Diagnostic result**

> "In the D/V/B visual coordinate experiment, representation Z separated the synthetic targets better than representation Q."

Never merge those statements.

## Why keep it?

Because a compact visual representation can still be useful even when it is not historical. It gives Omega a common diagrammatic language for:

- instantaneous state
- accumulated state
- interaction
- trajectory shape
- component-vs-combination comparisons

It is especially useful when explaining the recovered TIAMAT dynamics without pretending the visualization is the recovered firmware.
