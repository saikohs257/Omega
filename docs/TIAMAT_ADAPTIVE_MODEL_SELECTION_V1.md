# TIAMAT Adaptive Model Selection V1

## Purpose

TIAMAT keeps a broad candidate-observable library while preventing feature proliferation from becoming canonical state. Candidate combinations are treated as competing explanations and are selected only from held-out evidence.

## Candidate families

- Core latent candidates: damage, charge, recovery, momentum, residual momentum.
- Loading/context: forcing, baseline, pressure, tension, residual load, capacity, headroom.
- Motion: velocity, acceleration, jerk, flow, phase velocity/acceleration, impulse.
- Initial conditions: initial position, initial velocity, initial momentum, initial trajectory.
- Path geometry: path, trajectory, displacement, arc, curvature, path efficiency.
- Route/history: route, track, orbit, orbit period/drift, episode age, dwell, reversal, hysteresis, arrival context.
- Circuit/topology analogues: resistance, conductance, coupling, transfer pressure, connectivity.

Presence in the library is **not** evidence that a quantity is canonical.

## Selection protocol

1. Construct candidate models from the library.
2. Fit or score candidates only on the training partition.
3. Use validation data for model/threshold selection.
4. Evaluate the selected candidates once on a sealed test/holdout partition.
5. Report at minimum AUC, Brier score, log loss, stability, coverage and complexity.
6. Reject candidates that fail minimum evidence gates.
7. Use Pareto dominance so a larger model cannot win merely by adding variables without improving evidence.
8. Allow `UNRESOLVED` when no candidate passes.
9. Maintain multiple nondominated candidates when useful; do not force a single winner when evidence is contested.
10. Surface model disagreement as an observable diagnostic rather than hiding it.

## Consensus

Candidate models can emit probabilities for the same target. If their spread exceeds the configured tolerance, consensus is `CONTESTED`; TIAMAT must not silently collapse disagreement into a high-confidence decision.

## Authority boundary

Model selection is an **experiment/evidence layer**. A selected candidate does not automatically redefine the canonical TIAMAT state vector. Promotion requires the existing provenance, replay, conformance, and governance gates.

## Conceptual hypothesis under test

The current pseudocanonical hypothesis is that a compact latent core may include damage, signed loading/momentum and accumulated unresolved charge, with recovery/capacity and context potentially providing additional dimensions. Path, route, orbit, coupling, initial conditions and circuit analogues remain candidate observables until independent holdout evidence demonstrates incremental value.

## Required falsification

The selection machinery must be tested against synthetic worlds where candidate quantities are alternately causal, redundant, nonlinear, irrelevant and noisy. It must recover causal candidates while refusing to promote irrelevant ones. This prevents the discovery process from becoming a feature-hallucination engine.
