# TIAMAT Lite-3 — 25-Step Synthesis

Date: 2026-08-14

## Purpose
Compress the current head reconstruction without collapsing head-specific behavior or using final labels as predictors.

## 25-step evidence chain

1. Ground truth is the canonical 43,848-row Layer-1 timeseries with 453 episode starts.
2. H0 has 63 starts; H2 has 221; H3 has 169.
3. H0 is strongly hazard-dominant.
4. A simple H0 hazard boundary is already ~95.24% row-accurate at its best threshold.
5. A recovered ~0.92 H0 gate is simpler and more conservative than the best scan.
6. H0 hazard alone reaches mean LOYO AUC 1.000 across available yearly cells.
7. H2 hazard is the strongest single axis.
8. H2 hazard alone has AUC ~0.859.
9. H2 hazard+tempo reaches ~0.864 mean LOYO AUC.
10. H2 hazard+burden reaches ~0.863.
11. Adding a large feature set reduces stability; expansion is not justified.
12. H3 cannot share the H0 projection.
13. H3 raw hazard direction is inverted for the phasic target; absolute AUC ~0.735.
14. H3 temporal variables are stronger than recovery alone.
15. H3 hazard+tempo reaches ~0.793 mean LOYO AUC.
16. H3 hazard+burden reaches ~0.789.
17. H3 hazard+burden+tempo reaches ~0.802, the strongest compact tested reconstruction.
18. H3 recovery alone is weak.
19. A hard trapped boundary still leaves 10 H3 start mismatches.
20. 8/10 mismatches are in downtrend regime.
21. 9/10 have recovery_gate absent.
22. Mismatch shock median is ~0.626; failures are not simply extreme-shock cases.
23. Previous LiveDeficit is high in the residuals but not uniquely diagnostic.
24. Therefore H3 needs scoped temporal/recovery transition logic, not a universal burden threshold.
25. The correct compression target is three small head-specific projections, with H3 retaining temporal state.

## Lite-3 architecture

```text
shared sensors
    |
    +--> H0: hazard
    |
    +--> H2: hazard + tempo (burden optional pending further test)
    |
    +--> H3: hazard + burden + tempo
```

This is a reconstruction hypothesis, not canonical authority.

## Explicit non-goals

- Do not use `episode_type`, `duration_bucket`, or future entry path as predictors.
- Do not fit one universal scalar across H0/H2/H3.
- Do not promote the H2 compound gate as canonical without deterministic conformance.
- Do not tune H3 thresholds further before recovering the exact implementation inputs/intermediate values.

## Next maximum-discrimination experiment

For H3, locate the exact implementation inputs and compare intermediate values row-by-row against native saved labels. The 10 residual starts are the highest-value forensic sample because they concentrate in downtrend/recovery-gate-absent conditions and cannot be explained by shock magnitude alone.

For H2, run a direct leave-one-year-out comparison of hazard-only vs hazard+tempo vs hazard+burden on the same rows, then test whether tempo adds information independent of hazard.

For H0, freeze the hazard-dominant gate and stop expanding it unless new out-of-sample evidence breaks it.
