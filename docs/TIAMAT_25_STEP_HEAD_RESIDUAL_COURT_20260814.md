# TIAMAT 25-Step Head Residual Court

Date: 2026-08-14

Ground truth: `layer1_structured_hazard_arm_timeseries(15).csv` (43,848 rows, 453 episode starts)

## Result

This court keeps the heads separated and tests the decision boundary at the episode start.

### Population
- H0 `0_to_4`: 63 starts = 58 mixed, 5 trapped.
- H2 `2_to_4`: 221 starts = 160 mixed, 61 trapped.
- H3 `3_to_4`: 169 starts = 137 phasic, 25 mixed, 7 trapped.

## 1-5: Baselines

1. H0 threshold scan: best simple hazard threshold is ~0.958, row accuracy 95.24%; recovered ~0.92 gate remains a simpler and more conservative reconstruction.
2. H3 hard trapped boundary `hazard_score >= 0.966`: start-level agreement 94.08%; 10 starts remain mismatched.
3. H3 hard-boundary mismatches are concentrated in `down_gt10` (8/10), then `up_gt10` (2/10).
4. H3 hard-boundary mismatches are overwhelmingly `recovery_gate=absent` (9/10).
5. H3 hard-boundary mismatch shock median is ~0.626; it is not an obvious high-shock-only failure.

## 6-10: Single-axis discrimination

6. H2 trapped: hazard_score AUC 0.814; hazard history/peak 0.768; shock max 0.710.
7. H3 phasic: hazard_score raw direction is inverted for this target (absolute AUC 0.735); previous LD ~0.693; tempo48 ~0.686; hazard peak6 ~0.684.
8. H2 burden slope is weak (absolute AUC ~0.577).
9. H3 recovery alone is weak; it does not explain the lane.
10. H3 temporal/trajectory variables are stronger than raw burden, supporting a scoped temporal head rather than a universal scalar.

## 11-15: Leave-one-year-out minimal models

11. H2: `hazard + tempo` mean LOYO AUC ~0.864; `hazard + burden` ~0.863; hazard alone ~0.859. Adding everything reduces stability.
12. H3: `hazard + burden + tempo` mean LOYO AUC ~0.802; `hazard + tempo` ~0.793; `hazard + burden` ~0.789. This is the strongest tested compact H3 reconstruction, but it remains below source-level conformance.
13. H0: hazard alone remains extremely strong, mean LOYO AUC 1.000 across available yearly cells.
14. H2 feature expansion is not justified; the compact models outperform the larger feature set.
15. H3 benefits from temporal context, but no compact model reproduces the native tracker exactly.

## 16-20: Residual structure

16. The recovered hard H3 boundary leaves 10 start-level mismatches.
17. 8/10 are in downtrend regime.
18. 9/10 have `recovery_gate=absent`.
19. The mismatches are not concentrated at a single extreme shock value.
20. Previous-LD among those mismatches is high but not uniquely diagnostic; this argues against a simple burden-threshold fix.

## 21-25: Head specificity

21. H0 hazard dominates; adding generic burden/tempo is unnecessary.
22. H2 hazard is the strongest single axis; burden is secondary and useful only modestly OOS.
23. H3 cannot be explained by the same projection as H0/H2.
24. H2 compact comparison: `E+B` mean LOYO AUC ~0.863; `E+R` ~0.859; `E+tempo` ~0.864; `E+B+tempo` ~0.864.
25. H3 compact comparison: `E+B+tempo` ~0.802, `E+tempo` ~0.793, `E+B` ~0.789.

## Forensic conclusion

The evidence now supports:

```text
H0 = hazard-dominant entry classifier
H2 = hazard-dominant with modest burden/tempo context
H3 = temporally scoped recovery/phasic classifier
```

The important negative result is that adding a universal 4D latent vector does not solve the native head behavior. The remaining work is source-level reconstruction of each head's exact transition logic, not global feature expansion.

## Next discriminatory attack

For H3, recover the exact implementation inputs and compare intermediate values row-by-row against the native saved labels. Do not tune global thresholds until that source-level comparison is complete.

For H2, treat the recovered compound gate as a reconstruction only; do not promote it as canonical authority without deterministic conformance.

For H0, the simple hazard boundary is the strongest current survivor.
