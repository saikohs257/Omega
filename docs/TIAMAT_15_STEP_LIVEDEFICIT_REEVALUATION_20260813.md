# TIAMAT 15-Step LiveDeficit Re-evaluation — 2026-08-13

## Purpose

Re-evaluate the LiveDeficit/episode investigation using the canonical 43,848-row 2020–2024 Layer1 spine, recovered active-edge logic, historical/library archaeology, and causal proxy tests. This document separates source-backed facts from reconstruction hypotheses.

## Step results

1. **Canonical target:** `episode_type != none` is an active-state label, not an independent latent target.
2. **Active-state recovery:** recovered edge machine reproduces 4,026/4,026 active rows, 453/453 starts, and 453/453 exits.
3. **Recovered admission logic:** start on `delta(hazard_raw) > 1.00 AND LiveDeficit > 0.85 AND SimpleShock > 0.50`; exit on `delta(hazard_score) <= -0.17 AND SimpleShock[t-6] > 0.33`.
4. **Level-trigger falsification:** `hazard_score >= 0.70` misses 116 active rows; it is not the native admission mechanism.
5. **Entry-path producer:** normal shell is previous-hour LiveDeficit: `<=.70 -> 0_to_4`, `<=.85 -> 2_to_4`, `>.85 -> 3_to_4`.
6. **Exception:** one four-hour run (2021-05-04 02:00–05:00) is recorded as `2_to_4` even though previous-hour LiveDeficit is >.85. Treat as a native exception/override, not a formula-fix.
7. **Historical source archaeology:** the exact original `build_LiveDeficit()` and named `cum_*`/`raw_deficit` helpers were not recovered in the accessible corpus; forensic reports explicitly classify the surviving five-factor formula as proxy-level.
8. **Documented five-factor proxy:** 72h drawdown, 30d drawdown, 168h trend gap, OI level stress, OI value stress. Proposed weights 0.30/0.25/0.20/0.15/0.10 are not proven original.
9. **Static proxy test:** fixed five-factor proxy correlated only ~0.342 with native LiveDeficit using the tested normalization.
10. **Fitted static proxy:** constrained nonnegative weights improved full-sample correlation to ~0.561, dominated by 72h drawdown; trend-gap and OI-level weights collapsed to zero.
11. **Stateful proxy:** adding drawdown persistence/relief geometry and OI state improved retrospective correlation to ~0.714, with LOYO r ≈ 0.606/0.730/0.765/0.712/0.719 for 2020–2024. Still not generator recovery.
12. **Causal recursive replay:** a Ridge recurrence trained through 2023 and recursively replayed through 2024, using native LD only for the initial seed, achieved 2024 r ≈ 0.648, rho ≈ 0.649, MAE ≈ 0.188. This is substantially worse than the earlier leakage-prone ~0.996 one-step result and therefore is not a recovered generator.
13. **Downstream behavioral test:** substituting static or dynamic LD proxies into the recovered active-edge state machine caused ~8.6–8.5% of 2024 rows to disagree with native ACTIVE. Exact LD still matters at the admission boundary.
14. **LD gate role:** removing the current `LiveDeficit > .85` condition leaves 462 raw-jump+shock start candidates versus 453 native starts; all 453 native starts remain, but 9 false starts appear. Thus current LD acts as a selective admission veto after the hazard jump + shock trigger.
15. **Architectural conclusion:** current evidence favors a stateful, topology-aware latent system. The exact continuous LiveDeficit generator remains unresolved; its most defensible recovered role is as a structural-burden signal used both for admission gating and entry-path quantization, with downstream heads interpreting it differently by topology.

## Evidence boundaries

The repository reconciliation explicitly says historical SimpleShock, LiveDeficit, RecoveryWeakness_v1, hazard laws, hinge, damage/recovery/residual-load/momentum laws, and hysteresis rules are not runtime authority until source provenance plus deterministic conformance are established.

## Next decisive test

Do not chase a single scalar correlation. Recover or locate the original primitive source if possible. Otherwise reconstruct the minimum causal information needed to reproduce:

- active admission veto (`LiveDeficit > .85` at start),
- entry-path bucket boundaries,
- H2 burden/hazard interaction,
- H3 unresolved-load behavior,
- ExitBridge boundary behavior,
- cross-episode carry.

A candidate is promoted only when it passes these independent downstream courts and a clean recursive replay.
