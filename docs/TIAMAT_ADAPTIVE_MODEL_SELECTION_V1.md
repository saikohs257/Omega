# TIAMAT Adaptive Model Selection V1

## Purpose

TIAMAT keeps a broad candidate-observable library while preventing feature proliferation from becoming canonical state. Candidate combinations are competing explanations and are promoted only from held-out evidence.

## Candidate families

- Core latent: damage, charge, recovery, momentum, residual momentum.
- Loading/context: forcing, baseline, pressure, tension, residual load, capacity, headroom.
- Motion: velocity, acceleration, jerk, flow, phase velocity/acceleration, impulse.
- Initial conditions: initial position, initial velocity, initial momentum, initial trajectory.
- Path geometry: path, trajectory, displacement, arc, curvature, path efficiency.
- Route/history: route, track, orbit, orbit period/drift, episode age, dwell, reversal, hysteresis, arrival context.
- Circuit/topology analogues: resistance, conductance, coupling, transfer pressure, connectivity.

Presence in the library is **not** evidence that a quantity is canonical.

## Selection protocol

1. Construct candidate models from the library.
2. Fit/score candidates only on training data.
3. Use validation data for model and threshold selection.
4. Evaluate selected candidates once on a sealed holdout.
5. Report AUC, Brier, log loss, calibration error, stability, coverage and complexity.
6. Reject candidates that fail minimum evidence gates.
7. Use Pareto dominance across discrimination, calibration, stability and complexity.
8. Use bounded staged combination search rather than an unbounded power set.
9. Keep multiple nondominated candidates when useful; do not force a winner when evidence is contested.
10. Surface model disagreement as a diagnostic and permit `UNRESOLVED`.

## Combination search

`tiamat/combination_search.py` provides deterministic bounded enumeration and evidence-frontier extraction. Prediction generation remains outside the search layer so train/validation/holdout separation can be enforced by the caller. A candidate that requires a combination larger than the configured search bound is rejected rather than silently approximated.

## Metrics

- **AUC:** ranking/discrimination; higher is better.
- **Brier:** probabilistic accuracy/calibration; lower is better.
- **Log loss:** confidence-sensitive probabilistic error; lower is better.
- **Calibration error:** reliability of stated probabilities; lower is better.
- **Stability:** resistance to perturbation/split/regime changes; higher is better.
- **Complexity:** number of independent candidate axes; lower is preferred when evidence is otherwise equivalent.

No single metric is sufficient for promotion.

## Consensus

Candidate models can emit probabilities for the same target. If their spread exceeds the configured tolerance, consensus is `CONTESTED`; TIAMAT must not silently collapse disagreement into a high-confidence decision.

## Authority boundary

Model selection is an **experiment/evidence layer**. A selected candidate does not automatically redefine canonical TIAMAT state. Promotion requires existing provenance, replay, conformance and governance gates.

## Conceptual hypothesis under test

The current pseudocanonical hypothesis is that a compact latent core may include damage, signed loading/momentum and accumulated unresolved charge, with recovery/capacity and context potentially providing additional dimensions. Path, route, orbit, coupling, initial conditions and circuit analogues remain candidate observables until independent holdout evidence demonstrates incremental value.

## Required falsification

The selection machinery must be tested against synthetic worlds where candidate quantities are alternately causal, redundant, nonlinear, irrelevant and noisy. It must recover causal candidates while refusing to promote irrelevant ones. This prevents discovery from becoming a feature-hallucination engine.
