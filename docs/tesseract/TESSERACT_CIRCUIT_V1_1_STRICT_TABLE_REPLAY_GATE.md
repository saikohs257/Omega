# TESSERACT_CIRCUIT V1.1 Strict Table / Replay Gate

This specification defines the next executable gate after the recovered Q4 and V1.1 hand-built layers.

Status: IMPLEMENTATION TARGET — diagnostic/reference only; no runtime authority.

## Required sequence

Q4 legal edge → V1.1 hand-built components → strict circuit row → canonical runtime record → BentAxis identity/capsule → deterministic replay.

## Frozen prerequisites

- Q4 has 16 nodes and 32 undirected one-bit legal edges.
- HOLD_SELF is a control state, not a legal graph edge.
- Conductance uses the frozen train-risk-set smoothing rule.
- Ohms is inverse conductance with the frozen numerical cap.
- Future/realized edge labels are blocked from feature inputs.
- Learned edge weights are prohibited at this gate.
- Runtime authority remains outside this circuit reference layer.

## Replay invariant

Replaying an emitted circuit record must reproduce the same canonical semantic payload and identity-relevant state. Replay is reconstruction only; it cannot choose a new edge or grant authority.
