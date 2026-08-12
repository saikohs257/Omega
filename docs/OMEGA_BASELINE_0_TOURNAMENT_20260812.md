# Omega Baseline 0 — Synthetic Tournament

**Date:** 2026-08-12  
**Integration branch:** `integration/omega-assembled`  
**PR:** #29  
**CI merge revision tested:** `86ccda47ca9f269ad69b7a573595f8e5b1c03d99`  
**Python:** 3.11.15 and 3.12.13  
**Test suite:** 425 passed on each interpreter; 2 pytest collection warnings.

## Scope

This is the first frozen baseline for the assembled Omega/TIAMAT scientific machinery. It is **synthetic tournament evidence**, not empirical real-market validation.

The CI workflow explicitly runs the tournament scorecard, full evidence audit, Brier leaderboard, survivor stress, common held-out synthetic panel, expanded-world lab, adaptive mechanism discovery, controlled metric-disagreement report, focused TIAMAT tests, and the complete test suite.

## Core tournament

12 synthetic worlds:

- 8 selected
- 4 unresolved
- 0 failures

Winner counts:

- `state`: 2
- `A_x_B`: 1
- `calibrated`: 1
- `delayed`: 1
- `initial_momentum`: 1
- `path`: 1
- `resistance`: 1

### Interaction-only world

This is the key A×B diagnostic world.

| Candidate | AUC | Brier | LogLoss | Calibration error | Brier skill | Complexity | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 0.500000 | 0.452500 | 1.523513 | 0.450000 | -0.810000 | 1 | 20 |
| B | 0.500000 | 0.452500 | 1.523513 | 0.450000 | -0.810000 | 1 | 20 |
| **A_x_B** | **1.000000** | **0.009025** | **0.099820** | **0.095000** | **0.963900** | 2 | 20 |

This confirms that the synthetic benchmark contains a deliberately constructed interaction-only case where A and B individually carry no ranking signal while their combination does.

It does **not** establish the same relationship in real data.

## Common held-out synthetic panel

Round 3 uses a common held-out panel of **n=168** across seven surviving candidates.

| Candidate | AUC | Brier | LogLoss | Calibration error | Brier skill | Complexity |
|---|---:|---:|---:|---:|---:|---:|
| state | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |
| **A_x_B** | **1.000000** | 0.178200 | 0.540782 | 0.411429 | 0.287200 | 1 |
| calibrated | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |
| delayed | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |
| initial_momentum | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |
| path | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |
| resistance | 1.000000 | 0.175000 | 0.527483 | 0.400000 | 0.300000 | 1 |

The common synthetic panel therefore does **not** show A×B beating the strongest simple survivor. In the head-to-head comparison, `state` defeats A×B 1–0, while A×B loses to every other survivor except none; the remaining comparisons are ties because the synthetic panel deliberately collapses many candidates to identical outputs.

## Expanded-world discovery

22 synthetic worlds were evaluated:

- 21 known worlds
- 1 unknown world
- top-1 hit rate: **0.714286**
- top-k hit rate: **0.952381**
- ambiguity rate: **0.285714**
- known abstention: **0.000000**
- unknown abstention: **1.000000**

Adaptive mechanism discovery reported:

- adaptive top-k hit rate: **0.952381**
- static top-1 hit rate: **0.714286**
- average probes: **1.380952**
- early-stop rate: **0.238095**
- unknown abstentions: **1**

## Metric-governance observation

The controlled metric-disagreement report explicitly reports `NO_PRIMARY_METRIC=TRUE` and demonstrates that perfect AUC can coexist with materially worse probability quality. This is an implementation/governance result, not empirical validation.

## Interpretation

Baseline 0 establishes three things:

1. The assembled machinery can execute end-to-end in both supported Python versions.
2. The AUC/Brier/calibration machinery can distinguish ranking quality from probability quality and can expose interaction-only synthetic structure.
3. The current synthetic common held-out panel does **not** provide evidence that A×B is globally superior to simpler survivors.

Therefore the next scientific gate is **not tuning**. It is connecting this evaluation framework to the frozen real-data corpus/holdout path with the two honest controls and strict probability/label provenance.

No claim in this document promotes synthetic tournament behavior to canonical TIAMAT runtime authority.
