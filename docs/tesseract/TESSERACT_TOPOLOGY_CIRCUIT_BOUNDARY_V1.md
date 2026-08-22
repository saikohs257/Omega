# TESSERACT — Topology/Circuit Boundary V1

## Purpose

Close the evidence boundary between the recovered topology witness and the strict Q4 circuit formulation without assigning runtime authority.

## Contract

```text
TopologyWitness
    |
    | explicit declared edge
    v
Q4 legal-edge check
    |
    v
Strict circuit layer
```

The bridge may only admit an edge when:

1. the Q4 transition changes exactly one axis;
2. the topology witness explicitly declares the edge;
3. the topology witness is internally closed;
4. no runtime authority is granted by the bridge.

The bridge does **not** infer absent edges, reinterpret multi-axis jumps, select TIAMAT transitions, or promote TESSERACT evidence.

## Replay boundary

The accepted edge remains evidence until it enters the existing strict-circuit/capsule/replay path:

```text
TopologyWitness
  -> strict Q4 circuit row
  -> CircuitTraceCapsule
  -> BentAxis event
  -> ConstitutionalRecord
  -> TESSERACT_CIRCUIT_TRACE replay
```

This document is a boundary specification, not a claim that the complete integrated path has passed CI. CI remains the promotion evidence.
