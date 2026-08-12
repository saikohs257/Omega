# Omega DVQT Research Record

> Running lab notebook for the DVQT reverse-engineering investigation. Preserve raw results, interpretations, rejected hypotheses, implementation fixes, and unresolved questions so the work can later be reviewed as one coherent record.

## Current state

- Branch: `research/dvqt-reduction`
- Latest reviewed DVQT battery run checked out commit `266374ffa1a2c1b4f1f63a4178153b0a566b3175`.
- Focused DVQT tests: **22 passed**.
- Full repository tests on Python 3.12: **352 passed**, 2 pytest collection warnings.
- Ten-test directional battery executed successfully.

## Working question

We are reverse-engineering the hidden relationships among `D`, `V`, `B`, `tau`, `mode`, `phase`, and `history`.

The core question evolved from:

> What is the relationship between D and V/B/tau?

into the stronger question:

> Which variable carries genuinely directional, transition-relevant information after ordinary temporal persistence and shared structure are removed?

A second major question is:

> What is `B` actually doing relative to D and V: causal component, proxy, gate, redundant encoding, or interaction partner?

## Major implementation corrections

### Directional-gap correction

The original reverse-gap calculation compared commutative interactions in opposite operand order, so it could not establish temporal directionality. It was replaced by a temporal comparison of present source → future destination versus the reverse temporal ordering.

### Circular-lag leakage correction

The old lag path used `numpy.roll`, which wraps the end of a series back to the beginning. That contaminated temporal tests. The directional work now uses non-wrapping chronological alignment.

### Null-adjusted transfer

Raw transfer numbers were scale-contaminated, especially for `tau`. The experiment now reports:

- observed normalized conditional gain,
- circular-shift null median,
- excess = observed - null,
- paired directional asymmetry = forward excess - reverse excess.

The circular-source-shift null preserves source autocorrelation while destroying its alignment with the destination.

### Infrastructure fixes

Several CI/infrastructure defects were repaired during the investigation, including stale test signatures, missing `state_cartography` and `divergence_forensics` modules, packaging of `tools`, NumPy installation in CI, and sparse canonical-benchmark handling. Full CI is now capable of exercising the DVQT battery cleanly.

## Baseline model metrics

The main DVQT tournament currently reports:

| Candidate | Brier | Log loss | Calibration error | AUC | PR-AUC | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| **DVQT+B** | **0.0000** | **~0** | **0.0000** | **1.0000** | **1.0000** | **1.0000** |
| DVQT | 0.03158 | 0.08364 | 0.05742 | 0.89474 | 0.93539 | 1.0000 |
| DV+B | 0.15789 | 0.41820 | 0.28708 | 0.47368 | 0.67695 | 1.0000 |

The separate canonical tournament still exposes a sparse/per-world reporting issue in some runs; those NaNs must not be used as scientific evidence until independently validated.

## Inertia lab

Mean positive autocorrelation across 20 worlds:

| Variable | Mean positive autocorrelation | Mean half-life |
|---|---:|---:|
| D | 0.1349 | 1.00 |
| V | **0.1798** | 1.00 |
| B | **0.1772** | 1.00 |
| tau | 0.1399 | 1.00 |
| mode | **0.0591** | 1.00 |

Cross-lag response (mean absolute, lag 1..10):

| Direction | Value |
|---|---:|
| D→V | 0.0389 |
| D→B | 0.0393 |
| D→tau | 0.1762 |
| **D→mode** | **0.2984** |
| V→D | 0.0423 |
| V→B | 0.1313 |
| V→tau | 0.1686 |
| V→mode | 0.1963 |
| B→D | 0.0427 |
| B→V | 0.1307 |
| B→tau | 0.0829 |
| B→mode | 0.1290 |
| tau→D | 0.1763 |
| tau→V | 0.1706 |
| tau→B | 0.0812 |
| tau→mode | 0.1437 |
| mode→D | 0.2639 |
| mode→V | 0.1633 |
| mode→B | 0.1065 |
| mode→tau | 0.1458 |

Important implication: D is **not** the most inertial observable, yet it shows the strongest directional transfer into `mode`. That argues against a simple “most persistent variable drives the transition” explanation.

## Null-adjusted transfer lab

Aggregate excess transfer:

| Direction | Observed | Null | Excess |
|---|---:|---:|---:|
| D→V | 0.996515 | 0.996528 | **-0.000014** |
| D→B | 0.999253 | 0.999272 | **-0.000019** |
| D→tau | 0.999276 | 0.999326 | **-0.000050** |
| **D→mode** | **0.839281** | **0.711543** | **+0.127738** |
| V→D | 0.991293 | 0.991386 | -0.000092 |
| V→B | 0.999278 | 0.999267 | +0.000010 |
| V→tau | 0.999274 | 0.999271 | +0.000003 |
| V→mode | 0.744831 | 0.695562 | +0.049269 |
| B→D | 0.991305 | 0.991372 | -0.000067 |
| B→V | 0.996519 | 0.996501 | +0.000018 |
| B→tau | 0.999271 | 0.999278 | -0.000006 |
| B→mode | 0.718236 | 0.697194 | +0.021042 |
| tau→D | 0.991409 | 0.991588 | -0.000179 |
| tau→V | 0.996569 | 0.996583 | -0.000014 |
| tau→B | 0.999273 | 0.999261 | +0.000012 |
| tau→mode | 0.701689 | 0.700149 | +0.001540 |
| mode→D | 0.992008 | 0.991641 | +0.000367 |
| mode→V | 0.996753 | 0.996537 | +0.000216 |
| mode→B | 0.999273 | 0.999275 | -0.000003 |
| mode→tau | 0.999273 | 0.999292 | -0.000019 |

Directional asymmetries:

| Pair | Mean gap |
|---|---:|
| D→V vs V→D | +0.000079 |
| D→B vs B→D | +0.000048 |
| D→tau vs tau→D | +0.000129 |
| **D→mode vs mode→D** | **+0.127372** |
| V→B vs B→V | -0.000008 |
| V→tau vs tau→V | +0.000017 |
| **V→mode vs mode→V** | **+0.049053** |
| B→tau vs tau→B | -0.000019 |
| **B→mode vs mode→B** | **+0.021045** |
| tau→mode vs mode→tau | +0.001559 |

Top individual directional edges were dominated by D→mode:

- world_12: **+0.516720**
- world_15: **+0.289092**
- world_06: **+0.270341**
- world_05: **+0.268906**
- world_02: **+0.216743**
- world_16: +0.205555
- world_10: +0.193544
- world_08: +0.163143

Interpretation: D→V/B/tau mostly disappears under the autocorrelation-preserving null, while D→mode survives strongly.

## Ten-test directional battery

All 10 tests executed in `tools.dvqt_ten_tests`:

| # | Test | Result A | Result B | Interpretation |
|---|---|---:|---:|---|
| 1 | Lag scan | best lag index 6 | gap -0.002309 | dominant signal is not simply a lag-6 effect |
| 2 | Reverse check | 6 | -0.002309 | agrees with lag-scan control |
| 3 | Leave-one-world-out | 0.107276 | 0.134323 | signal persists when worlds are held out |
| 4 | Sign consistency | 1.0 | 0.089174 median gap | all worlds preserve positive sign |
| 5 | Null z | 2.8086 | 2.7098 | signal exceeds circular-null expectation |
| 6 | Block null | 0.136975 | 0.103391 | robust to block-style surrogate |
| 7 | Destination specificity | 0.127738 | -0.0000137 | mode is the distinctive destination |
| 8 | Source specificity | 0.127738 | 0.049269 | D is strongest source into mode |
| 9 | Conditional persistence | 0.127738 | 0.089461 | effect survives conditioning/persistence check |
| 10 | D ablation | 0.147546 | 0.102932 | D removal changes the directional result substantially |

### Important caution about tests 7-10

These are supportive, not causal proof. They establish a robust pattern of directional predictive information under several surrogate/conditioning designs, but the experiment remains an observational temporal-information test.

## Relationship map

Across worlds, the strongest nonlinear relationship remains **D+V**, with representative interaction AUC values around 0.92–0.96. The top aggregate relationship seen in the lab is approximately:

- D+V interaction AUC: **0.9490**
- interaction gain: **0.1216**
- temporal reverse gap: **+0.0558** in the strongest promoted world

This is distinct from the null-adjusted transfer finding: **D and V can jointly encode a strong interaction without D unidirectionally predicting V.**

That distinction is central to the working hypothesis that D and V may be different projections of a shared hidden mechanism, with D being more transition-relevant.

## Expanded mechanism-selection lab

22 worlds, 21 known + 1 unknown.

- static top-1 hit rate: **0.714286**
- adaptive top-k hit rate: **0.952381**
- ambiguity rate: **0.285714**
- unknown-world abstention: **100%**
- adaptive average probes: **1.380952**
- adaptive early-stop rate: **0.238095**

The selector successfully switches among mechanism families including proximity, momentum, acceleration, resistance, path, hysteresis, phase, recovery, and coupling. This supports the broader interpretation that the synthetic worlds contain distinct mechanistic regimes rather than one universal scalar relationship.

## Important observed mechanisms / clues

### D→mode looks like a transition pathway

D has moderate persistence but is much more directional into `mode` than into V/B/tau. This suggests D may be closer to a hidden controller/state variable than a purely descriptive sensor.

### D×V is a joint mechanism, not a simple arrow

The interaction AUC is very high while directional D→V excess is approximately zero. This argues for coupled state representation rather than a simple D-causes-V story.

### tau is not the sole reservoir

tau has moderate inertia and nearly reciprocal D↔tau transfer. The current evidence does not support tau as a uniquely upstream driver.

### B deserves focused reverse engineering

B boosts the main DVQT benchmark dramatically when added to DVQT, and B repeatedly participates in nonlinear relationships with V/D. But the directional battery shows B→mode at only +0.0210, far below D→mode. B may therefore act as a gate, proxy, interaction term, or encoded state component rather than the primary directional driver.

## Hypotheses — current ranking

### H1 — D is transition-relevant hidden-state information

D may encode a latent quantity that is directly involved in the transition into `mode`.

**Status:** strongly supported by current temporal-transfer battery, but not causal proof.

### H2 — D and V are complementary projections of a shared hidden state

The strong D×V interaction combined with negligible directional D→V excess fits this model well.

**Status:** promising.

### H3 — B is a gate/interaction component

B may not drive mode directly but may change how D/V combine or how the system resolves a state.

**Status:** unresolved and high priority.

### H4 — tau is a consequence/reciprocal state rather than the primary trigger

D↔tau is nearly symmetric after null adjustment.

**Status:** plausible.

## Rejected / weakened hypotheses

### “The most inertial variable is the driver”

Weakened. V and B have higher autocorrelation than D, but D has stronger directional transfer into mode.

### “D drives V”

Weakened strongly. Null-adjusted D→V is approximately zero and D→V vs V→D asymmetry is only +0.000079.

### “tau is the main upstream reservoir”

Weakened. tau→mode is only +0.001540 aggregate, with near-symmetric D↔tau behavior.

## CI / implementation history

The investigation encountered and repaired multiple CI failures. The most important ones were:

1. directional-gap argument-order mismatch;
2. commutative reverse-gap implementation;
3. circular `np.roll` lag leakage;
4. missing `tiamat.state_cartography`;
5. missing `tools.divergence_forensics`;
6. missing `tools` packaging path;
7. missing NumPy in CI environment;
8. sparse canonical-benchmark NaN/zero-coverage behavior;
9. stale workflow execution against earlier commits;
10. directional regression fixture semantics.

These were repaired rather than suppressed, and the final reviewed battery passed the focused and full test suites.

## Current unresolved questions

1. **What exactly is B?** Proxy, gate, interaction term, redundant encoding, or direct component?
2. Can D be decomposed into a component shared with V and a residual component that uniquely predicts mode?
3. Does the D→mode signal survive a multivariate model containing D, V, B, tau, phase, and history simultaneously?
4. Is D→mode still present under stricter out-of-world validation with no shared generator family?
5. Does intervention on B change the D→mode pathway or only overall prediction quality?
6. Does the directionality depend on phase/regime, or is it globally stable?
7. Can the latent mode transition be reconstructed from D/V/B without directly observing `mode`?

## Next planned experiments

### 1. Residual-D decomposition

Regress/remove the component of D explainable by V/B/tau/history, then retest residual-D→mode.

### 2. B intervention matrix

Run B at fixed levels and test whether D→mode transfer changes, reverses, or remains invariant.

### 3. Full conditional directional graph

Estimate all ordered edges using a multivariate baseline containing each destination's own history plus all other candidate sources.

### 4. Hidden-state reconstruction

Try to predict `mode` from D/V/B/tau/history without using mode itself, then inspect which features are indispensable.

### 5. World-family holdout

Leave out entire generator/mechanism families rather than individual worlds to test transfer of the inferred relationship.

## Review discipline

Do not treat any single AUC, interaction score, or directional gap as causal proof. Prefer effects that:

- survive an explicit null;
- persist across held-out worlds;
- are directionally asymmetric;
- are destination/source specific;
- survive conditioning;
- replicate across alternative surrogate constructions;
- do not depend on circular alignment or stale artifacts.

## Raw evidence pointers

Primary evidence is retained in the GitHub Actions logs for the DVQT research branch, including the run that executed `tools.dvqt_ten_tests`, `tools.dvqt_transfer_lab`, `tools.dvqt_relationship_lab`, `tools.dvqt_inertia_lab`, `tools.dvqt_b_fingerprint`, and the full pytest suite.

---

_Last updated: 2026-08-12. This file is intended to be appended/updated as the investigation proceeds._
