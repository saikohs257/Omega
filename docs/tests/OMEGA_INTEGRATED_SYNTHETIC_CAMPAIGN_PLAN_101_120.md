# OMEGA Integrated Synthetic Campaign — Steps 101–120

**Date:** 2026-08-21  
**Status:** TEST PLAN / EXECUTION GATE  
**Purpose:** Convert the recovered architecture into an executable, reproducible synthetic campaign without promoting research mechanisms.

## 101. Canonical test manifest
Freeze the component set under test: CHUG family, Hinge/HF8/HF9 where recoverable, Seam, Attack, Release, Capacity, Exit Latch, BAGE/CARR, HYDRA heads, Oracle fusion, TIAMAT, ERK, Court, BentAxis, Tesseract/Tesseract_Circuit.

## 102. Evidence classes
Every output is classified as `OBSERVATION`, `INFERENCE`, `FUSION`, `STATE`, `EVALUATION`, or `AUTHORITY`. No implicit promotion.

## 103. Synthetic truth isolation
Latent truth is generated independently of every tested mechanism. No component receives truth labels as runtime inputs.

## 104. Deterministic seed matrix
Use fixed seeds and publish the seed/corpus manifest. Identical seed + version must reproduce identical outputs.

## 105. Scenario generation
Generate controlled cases for false calm, ignition, failed reset, recovery inversion, ceiling/hazard, exit, carry, cross-episode transfer, simultaneous ENTER/EXIT, and contradictory evidence.

## 106. Noise/missingness sweep
Repeat scenarios across clean, noisy, delayed, missing, and partially observed telemetry.

## 107. Sidecar isolation baseline
Run each sidecar alone to establish its standalone detection surface. Do not use this as an authority ranking.

## 108. Pairwise complementarity
Run all important sidecar pairs and measure incremental detections, conditional information, and disagreement.

## 109. Collective complementarity
Run the full sidecar set and compare information retained against all leave-one-out configurations.

## 110. Correlated-evidence test
Create multiple mechanisms sharing the same underlying feature. Verify that agreement is not falsely counted as independent evidence.

## 111. Independent-convergence test
Create genuinely independent evidence channels converging on the same latent transition. Measure whether Oracle can distinguish independent convergence from correlated agreement.

## 112. DIC representation test
Represent the sidecar outputs as distributed inference records with source identity, path, timestamp, strength, confidence, and provenance. Do not invent a separate DIC execution engine.

## 113. Oracle preservation test
Verify that Oracle fusion preserves contributing evidence identities and disagreement rather than reducing the collective to an opaque scalar.

## 114. Oracle fusion comparison
Compare the recovered/implemented Oracle fusion behavior against simple alternatives: majority vote, weighted average, max-score selection, and unfused evidence. Any superiority claim must be empirical.

## 115. HYDRA path test
Run H0 FalseCalmIgnition, H2 ResetDragRelease, H3 RecoveryInversion, H4 CeilingTrap, ExitBridge, and Carry against path-specific synthetic cases. Preserve historical dispositions such as H4 scout-only.

## 116. TIAMAT ownership test
Assert that only TIAMAT may mutate canonical structural state. Sidecars and Oracle may produce evidence/fusion but cannot directly alter canonical state.

## 117. Temporal causality test
Verify that no feature uses information unavailable at decision time, especially episode-end values, HFLUX, carry, and any retrospective HF9 machinery.

## 118. Replay equivalence test
Run live-style generation and deterministic replay. Require identical evidence, fusion, TIAMAT transition, and BentAxis provenance.

## 119. Shadow-controller scan
Instrument state mutation and authority changes. Any sidecar, Oracle subcomponent, ERK component, Tesseract component, or other analytical mechanism that independently changes canonical state is a failure.

## 120. Campaign gate
Only after 101–119 pass may the full 200-scenario campaign run. The gate reports `PASS`, `PASS_WITH_RESTRICTIONS`, `FAIL_COMPONENT`, `FAIL_INTEGRATION`, or `UNKNOWN`. Synthetic success does not authorize real-world promotion.

## Non-negotiable invariants

1. Historical implementation != canonical implementation.
2. DIC terminology does not imply a separate executable subsystem without source evidence.
3. Sidecar != controller.
4. Prediction quality != authority.
5. ENTER and EXIT remain potentially orthogonal.
6. Disagreement is preserved.
7. Correlated consensus is not treated as independent evidence.
8. Oracle fusion must remain inspectable.
9. TIAMAT remains the canonical structural-state owner unless evidence falsifies that claim.
10. BentAxis records provenance; it does not establish truth.
11. Tesseract topology does not itself authorize TIAMAT transitions.
12. Research/shadow mechanisms remain non-authoritative until separate validation and Court adjudication.
