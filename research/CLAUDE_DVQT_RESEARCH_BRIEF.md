# Claude Handoff — Omega DVQT Reverse Engineering

## Mission
Reverse-engineer the hidden relationships among `D`, `V`, `B`, `tau`, `mode`, `phase`, and history in Omega's synthetic DVQT worlds. The goal is not merely prediction; it is to identify which variables carry independent, directional, transition-relevant information and reconstruct the hidden mechanism.

## Current evidence

### Main benchmark
- DVQT+B: Brier 0.0000, Log loss ~0, calibration error 0.0000, AUC 1.0000, PR-AUC 1.0000.
- DVQT alone: Brier 0.03158, Log loss 0.08364, calibration error 0.05742, AUC 0.89474, PR-AUC 0.93539.
- DV+B is much weaker.
- Treat perfect synthetic scores cautiously; they may indicate target leakage/encoding or a deliberately easy benchmark.

### Inertia
Mean positive autocorrelation: V 0.1798, B 0.1772, tau 0.1399, D 0.1349, mode 0.0591.

Important: D is not the most persistent variable, yet it has the strongest directional relationship with mode.

### Null-adjusted directional transfer
The experiment now compares conditional predictive gain against an autocorrelation-preserving circular-shift null.

Aggregate excess:
- D -> V: -0.000014
- D -> B: -0.000019
- D -> tau: -0.000050
- D -> mode: +0.127738
- V -> mode: +0.049269
- B -> mode: +0.021042
- tau -> mode: +0.001540

Directional asymmetry:
- D -> V vs V -> D: +0.000079
- D -> B vs B -> D: +0.000048
- D -> tau vs tau -> D: +0.000129
- D -> mode vs mode -> D: +0.127372

Top D->mode world gaps include approximately +0.517, +0.289, +0.270, +0.269, +0.217.

### Ten-test directional battery
1. Lag scan: best lag index 6, gap -0.002309; this argues against a simple fixed-lag explanation.
2. Reverse check at that lag: -0.002309.
3. Leave-one-world-out: roughly +0.107 to +0.134.
4. Sign consistency: 100% positive.
5. Circular-null z: mean ~2.81, median ~2.71.
6. Block null: mean excess +0.136975.
7. Destination specificity: D->mode +0.127738 while D->V/B/tau ~0.
8. Source specificity: D->mode +0.127738 vs V->mode +0.049269.
9. Conditional persistence: +0.127738.
10. D ablation: mean +0.147546; treat as supportive, not causal proof.

### Relationship structure
D+V remains the strongest nonlinear interaction, with representative interaction AUC around 0.949 and interaction gain around 0.122. This coexists with essentially zero null-adjusted D->V transfer.

Interpretation: D and V may be complementary projections of a shared hidden state rather than a simple directed pair.

## Current hypotheses

### H1 — D is transition-relevant hidden-state information
Strongly supported as a temporal predictive hypothesis; not causal proof.

### H2 — D and V are complementary projections of a shared hidden state
Promising because joint interaction is strong while directional D->V is near zero.

### H3 — B is a gate/context/interaction component
Unresolved. B materially improves DVQT+B, but direct B->mode excess is much smaller than D->mode.

### H4 — tau is reciprocal/downstream state rather than primary trigger
Plausible; D<->tau is nearly symmetric and tau->mode is weak.

## Important methodological corrections already made
- Replaced commutative operand-swapping reverse-gap with temporal directional comparison.
- Removed `numpy.roll` wraparound leakage from lag tests.
- Added conditional/null-adjusted transfer rather than relying on raw transfer scores.
- Fixed stale test signatures and directional regression fixtures.
- Repaired missing modules/packaging/CI dependencies and sparse benchmark handling.
- Full reviewed battery reached 352 tests passed on Python 3.12; focused DVQT battery 22 passed.

## What NOT to do
- Do not call the D->mode result causal.
- Do not tune thresholds simply to make CI green.
- Do not use raw tau transfer values without scale/null controls.
- Do not interpret the separate sparse canonical scoreboard's historical NaNs as scientific evidence.
- Do not assume B is causal merely because DVQT+B is perfect.

## Highest-value next experiments

### A. Residual-D decomposition
Remove the component of D predictable from V, B, tau, and D-history. Test whether residual D still predicts future mode under the same null-adjusted protocol.

### B. B decomposition
Predict B from D/V/tau/history; define B residual. Test whether B-residual improves mode prediction and/or changes D->mode transfer.

### C. B intervention matrix
Compare real B, shuffled B within world, time-reversed B, phase-shifted B, fixed B, DV-predicted B, and residual B. Measure both benchmark performance and D->mode excess.

### D. Full conditional directional graph
For each destination, compare source-augmented model against destination-history-only baseline while conditioning on all other candidate variables. Use the same null construction.

### E. Transition-centered analysis
Define mode-transition events and inspect D/V/B/tau trajectories over a pre-transition window. Test whether D changes before B, B before D, or both respond to a hidden variable.

### F. Family-level holdout
Hold out whole mechanism families, not individual worlds, and test whether D->mode survives generator-family transfer.

## Desired output from Claude
1. Challenge the hypotheses above.
2. Identify leakage/confounding possibilities we may have missed.
3. Propose the smallest set of experiments that most sharply distinguishes H1-H4.
4. Pay particular attention to whether B is a gate, proxy, or encoded target.
5. Prefer falsification tests over more score accumulation.
6. Preserve exact metrics and negative results in the lab notebook.

## Canonical record
The full running record is `research/DVQT_RESEARCH_RECORD.md`. Treat it as the source of accumulated evidence and append new validated findings rather than replacing old results.
