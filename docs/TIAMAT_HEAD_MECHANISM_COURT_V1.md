# TIAMAT Head Mechanism Court V1

Status: research-only evidence record. No head receives runtime authority from this court.

## Purpose

This court separates two questions that were previously being mixed:

1. **Historical head-seat performance**: how the recovered head behaves on its own historical target set.
2. **Common structural survival performance**: how simple state-derived scores behave on a common 15-hour Stage-4 persistence target.

These are different experiments and must not be conflated.

## Historical head-seat evidence

The recovered historical full court reports the following route-local results:

| Head | N | Positive | AUC | AP |
|---|---:|---:|---:|---:|
| H0 / 0→4 | 12 | 7 | 0.9429 | 0.9617 |
| H2 / 2→4 | 42 | 29 | 0.9337 | 0.9727 |
| H3 / 3→4 | 19 | 12 | 0.9643 | 0.9833 |
| H4 / 4→4 | 567 | 495 | 0.7713 | 0.9642 |

These are the historical head-local targets from the May/June reconstruction corpus. H3 is the strongest of the three narrow entry heads in that court.

## Common 15-hour structural survival court

Using the 43,848-row 2020–2024 runtime panel and a new common target of surviving the next 15 contiguous hourly observations in Stage 4:

| Seat | N | Positive | AUC | AP | Min yearly AUC |
|---|---:|---:|---:|---:|---:|
| 0→4 | 63 | 0.190 | 0.8775 | 0.5907 | 0.7778 |
| 2→4 | 221 | 0.186 | 0.7340 | 0.4112 | 0.5208 |
| 3→4 | 169 | 0.101 | 0.6687 | 0.1547 | 0.5067 |
| 4→4 | 3573 | 0.404 | 0.8139 | 0.7182 | 0.7493 |

This common target is **not** the historical published CP15 label. It is a structural comparator only.

## Simple mechanism ablation on the common target

Scores tested were intentionally simple and not optimized:

- LiveDeficit
- hazard_raw
- SimpleShock
- LiveDeficit + 0.2·hazard_raw
- LiveDeficit + 0.1·SimpleShock
- LiveDeficit + 0.2·hazard_raw + 0.1·SimpleShock

AUC results:

| Seat | LD | hazard_raw | SimpleShock | LD+0.2h | LD+0.1shock | LD+0.2h+0.1shock |
|---|---:|---:|---:|---:|---:|---:|
| 0→4 | 0.815 | 0.818 | 0.683 | 0.840 | 0.814 | **0.843** |
| 2→4 | 0.734 | 0.832 | 0.710 | 0.857 | 0.739 | **0.864** |
| 3→4 | 0.716 | 0.806 | 0.657 | 0.813 | 0.735 | **0.819** |
| 4→4 | 0.823 | 0.793 | 0.706 | 0.811 | 0.830 | **0.814** |

The common-target court therefore suggests:

- **H0:** combined burden + hazard information is stronger than either alone.
- **H2:** hazard_raw adds substantial information; the combined score is strongest of the simple tested forms.
- **H3:** hazard_raw is materially stronger than LiveDeficit alone on this common target, but the seat remains strongly target/regime-sensitive.
- **H4:** SimpleShock adds more than hazard_raw in the simple tested blend; the seat is fundamentally different from entry seats.

## Exit / timing seats

On 453 historical exits, predicting whether another Stage-4 entry occurs within a future horizon:

| Target | ExitBridge AUC | PriorCarry AUC |
|---|---:|---:|
| next trigger within 6h | 0.7835 | 0.5724 |
| next trigger within 24h | 0.7363 | 0.5290 |
| next trigger within 48h | 0.7129 | 0.5096 |

Interpretation: the currently reconstructed **ExitBridge** signal has materially more timing information than the simple prior-exit carry score. PriorCarry remains a memory mechanism; these numbers do not justify treating it as an independent predictor.

## Historical topology facts

The full 43,848-row panel contains:

- 63 strict 0→4 transitions
- 221 strict 2→4 transitions
- 169 strict 3→4 transitions
- 3,573 strict 4→4 rows
- 453 runs / episode starts

The recovered entry-path mapping reproduces the historical 453 starts exactly. The path is determined from the previous-hour burden with the known prior-shock correction for the high-burden boundary.

## Conclusions

1. The historical system is genuinely multi-head and does not collapse cleanly to one universal scalar.
2. H3 remains the strongest narrow entry head in the **historical head-local court**; its lower AUC in the common 15-hour survival court does not contradict that because the target is different.
3. H4 has the broadest support and behaves differently from entry heads: persistence/release is the relevant mechanism.
4. ExitBridge is supported as a timing-seat mechanism; PriorCarry should remain classified as memory rather than promoted to a generic predictor.
5. No head should be promoted to runtime authority from these scores alone. The next evidence gate is intervention/ablation against the **head-local historical targets**, with untouched-year or leave-one-year-out checks and explicit contamination tests.

## Non-goals

- Do not use BVD/DVB as canonical state.
- Do not reconstruct the missing native LiveDeficit generator from these results.
- Do not relabel structural scores as probabilities.
- Do not merge head-local and common-target AUCs into one leaderboard.
