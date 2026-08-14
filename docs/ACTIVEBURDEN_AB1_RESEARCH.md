# ActiveBurden AB-1 Research Checkpoint

## Status

**Candidate only — not canonical.**

Claude proposed:

```text
ActiveBurden_AB1 = 0.6 * hazard_score + 0.4 * LiveDeficit
```

A reported AUC of 1.000 was obtained against `episode_type_active`, where:

```python
episode_type_active = (episode_type != "none")
```

That is an oracle-derived target and therefore is **not independent validation**. The 1.000 result is preserved as a discovery clue, not proof of the original scalar.

## Required validation court

1. Evaluate AB-1 on causal future transition targets for H2 and H3.
2. Test ExitBridge timing at 6h, 24h, and 48h.
3. Test PriorCarry independently from current/live `LiveDeficit`.
4. Validate H4 only on fresh legitimate `4_to_4` rows using `cp15_LiveDeficit`; never manufacture 4→4 rows from `episode_type`.
5. Run strict leave-one-year-out validation.
6. Audit every candidate feature for future/label leakage.
7. Compare 1D, 2D, 3D, 4D, and 5D state representations.
8. Compare universal projections against topology-specific projections.
9. Inspect exact disagreement rows rather than optimizing only aggregate AUC.

## Candidate 4D state

Claude's proposed state components are:

```text
z_accumulated_burden = LiveDeficit
z_unresolved_load    = max(LiveDeficit - SimpleShock, 0)
z_hazard_elevation   = hazard_score
z_recovery_capacity  = 1 - RecoveryWeakness_v1
```

These are **derived observables**, not yet demonstrated latent variables. Do not call the resulting series canonical until dimensionality and causal/OOS tests support it.

## Important distinction

Current/live deficit and previous-episode carry must remain separate. A prior result showed positive current/live deficit behavior in 2→4 while `prev_exit_live_deficit` could invert. This may indicate topology-, timing-, or boundary-dependent semantics.

## H4 guardrail

The current 4→4 `cp15_LiveDeficit` separation is a candidate topology-completion result. Do not hard-code the approximately 0.34 threshold or promote it to runtime until fresh aligned 4→4 data satisfies the frozen promotion criteria.

## Goal

Find the **smallest causal state representation** that survives topology, duration, boundary timing, carry, and out-of-sample tests. If AB-1 fails, preserve the failure as evidence rather than tuning it until it wins.
