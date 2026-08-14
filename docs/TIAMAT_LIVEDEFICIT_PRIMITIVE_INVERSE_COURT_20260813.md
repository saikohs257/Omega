# TIAMAT LiveDeficit Primitive Inverse Court — 2026-08-13

## Purpose
Test the surviving forensic specification of LiveDeficit against the native 43,848-row 2020–2024 Layer-1 spine without pretending the missing original generator has been recovered.

## Source-supported specification
The forensic recovery reports describe LiveDeficit as a normalized blend of:

- 72h drawdown
- 30d drawdown
- 168h trend gap
- OI level stress
- OI value stress

A later proxy handoff supplies weights 0.30 / 0.25 / 0.20 / 0.15 / 0.10. These are explicitly marked proxy-level, not proven original source.

## Empirical test
Using the canonical 2020–2024 spine, the three price-only components were constructed from the verified close series and tested under raw, rolling robust-z, and rolling percentile normalization. A regression fit to native LiveDeficit was evaluated in-sample and leave-one-year-out.

### Results

| Representation | Pearson r | Spearman rho | MAE |
|---|---:|---:|---:|
| Raw price stress | 0.564 | 0.544 | 0.153 |
| Robust-z stress | **0.639** | **0.593** | **0.141** |
| Percentile stress | 0.575 | 0.560 | 0.152 |

Best representation, robust-z, leave-one-year-out Pearson correlation:

- 2020: 0.615
- 2021: 0.627
- 2022: 0.573
- 2023: 0.462
- 2024: 0.553

## Interpretation

The three price-only ingredients are insufficient to explain canonical LiveDeficit. This is consistent with the historical specification assigning 25% of the proxy blend to OI level/value stress.

The test therefore **does not falsify the documented five-component hypothesis**; it shows that the OI side is potentially decisive and that a price-only reconstruction is inadequate.

## OI evidence
Library search recovered source/UI artifacts showing historical tooling expected hourly OI fields `sumOpenInterest` and `sumOpenInterestValue`, but the available local 2020–2024 OHLCV source does not contain those fields. Binance historical Open Interest tooling also documents limited retention for direct retrieval, so absence of OI in the current local spine is a data-availability problem, not evidence that OI was not part of the historical formula.

## Provenance boundary
The forensic recovery report explicitly states that the exact original `build_LiveDeficit()` was not found. Treat all normalized-blend weights and kernel details as hypotheses/proxy reconstruction until independently reproduced.

## Next court
1. Recover a historical 2020–2024 OI series from archived artifacts or a surviving data package.
2. Construct OI level stress and OI value stress with multiple causal normalization variants.
3. Fit only the unknown normalization/kernel, holding the five documented ingredients and proxy weights as controlled hypotheses.
4. Require LOYO stability and full-series residual inspection before promoting any formula.
5. Once the primitive is stable, replay the exact recovered active edge machine and check the single 2021-05-04 entry-path exception.
