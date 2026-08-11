# TIAMAT Reduction Falsification Protocol V1

## Hypothesis

Treat `(D, V, q, tau_q)` as a research-only reduced state hypothesis. It does not replace the canonical TIAMAT state machine.

## Competing models

- Reduced: `D, V, q, tau_q`
- Reduced+Recovery: `D, V, R, q, tau_q`
- Full: existing TIAMAT evidence/state representation

## Primary questions

1. Does the reduced state predict held-out mode transitions as well as the full state?
2. Does explicit recovery add incremental predictive information after conditioning on `(D, V, q, tau_q)`?
3. Are observed transitions concentrated near reproducible boundaries in reduced phase space?
4. Are there episodes where damage and recovery move independently, falsifying `R = -min(V, 0)`?

## Falsification rules

A result is a falsification when the pre-registered reduced model loses on an untouched evaluation split by a material margin that is stable across repeated blocks. Do not retune thresholds on the evaluation split.

### H1: independent damage/recovery

Search for observations where `D` rises while independently measured recovery also rises. Such an episode falsifies the strict identity `R = -min(V, 0)`.

### H2: incremental information

Compare transition prediction using the reduced state with the reduced+recovery and full representations. A robust improvement from the additional variables is evidence that the reduced state is insufficient.

### H3: phase-space guard geometry

Measure `(D, V, tau_q)` at every observed transition on held-out data. Test whether transitions cluster near stable boundaries rather than throughout the interior of a mode region.

## Data separation

All coefficient fitting and threshold selection must occur before the final evaluation split. The evaluation split is for falsification only.

## Interpretation

- Reduced wins: evidence for dimensional reduction, not proof of ontology.
- Augmented/full wins: identify the smallest additional variable set that explains the gain.
- No stable winner: retain the richer representation and report non-identifiability.
