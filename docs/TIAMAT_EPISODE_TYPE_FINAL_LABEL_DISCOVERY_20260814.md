# TIAMAT Episode-Type Label Semantics Discovery

Date: 2026-08-14
Ground truth: `layer1_structured_hazard_arm_timeseries(15).csv` (43,848 hourly rows, 453 episodes)

## Finding

`episode_type` in the native Layer-1 spine behaves as a **final/stabilized episode classification**, not a purely causal label assigned at the episode's first hour.

Evidence:

- Native H3 (`3_to_4`) starts: 169 episodes.
- Their start-row types are: 137 phasic, 25 mixed, 7 trapped.
- Across all 453 episodes, final type counts are 137 phasic, 243 mixed, 73 trapped.
- H3 trapped examples can begin below the reconstructed `hazard_score >= 0.966` boundary (for example 0.964429 and 0.952574), yet persist for many hours.
- H3 mixed examples can begin above 0.966 (including several `0.970688` cases), showing that `0.966` is not a canonical universal start-time trapped threshold.
- H3 phasic episodes have maximum native age <= 8h, while mixed episodes observed here span 1–23h and trapped episodes begin at 9h and extend much longer.

## Why previous H3 tests looked contradictory

The recovered tracker classifies a **provisional episode type at entry** and later reclassifies phasic runs to trapped after the 8h persistence boundary.

The native `episode_type` field, however, is already the stabilized label propagated through the episode. Therefore comparing a causal entry-time gate directly against the native final `episode_type` label at the first row introduces a temporal mismatch.

This explains apparent contradictions such as:

- native `hazard_score=0.952574` + final `episode_type=trapped`
- native `hazard_score=0.970688` + final `episode_type=mixed`

Those are not evidence that the recovered H3 tracker threshold is random. They show that the native label contains episode-level future/persistence information.

## Implication for reverse engineering

The correct forensic separation is now:

```text
ENTRY ROUTER
    -> selects 0_to_4 / 2_to_4 / 3_to_4

PROVISIONAL HEAD DECISION
    -> initial phasic / mixed / trapped state

PERSISTENCE / EPISODE RECLASSIFICATION
    -> stabilizes the final episode_type

NATIVE episode_type
    -> final episode-level label, not a pure entry-time causal target
```

Therefore:

1. Do not use native `episode_type` as an instantaneous causal target when reconstructing the entry gate.
2. Validate the H3 **provisional entry decision** separately from the subsequent persistence/reclassification logic.
3. Treat the recovered `hazard_score >= 0.966` rule as a tracker reconstruction invariant, not canonical source authority.
4. The remaining 98.02% tracker-vs-native gap should now be decomposed into entry-state error versus episode-persistence/reclassification error.

## Next experiment

Build a two-stage conformance court:

### Stage A — Entry state

Compare the recovered H0/H2/H3 entry gates using only information available at the episode start.

### Stage B — Episode state evolution

Starting from the provisional entry state, replay persistence/reclassification hour by hour and compare against the native final label and age trajectory.

This should identify whether remaining discrepancies are caused by:

- incorrect entry gate,
- incorrect persistence boundary,
- incorrect reset/exit handling,
- or an upstream primitive mismatch.

## Evidence classification

**Strongly supported:**
- native `episode_type` is episode-level/stabilized in behavior;
- H3 start rows cannot be interpreted as a clean causal label for the final type;
- the 0.966 threshold is a reconstructed tracker rule, not a proven canonical universal boundary.

**Unresolved:**
- exact original entry-time H3 classifier;
- exact native persistence/reclassification rule;
- whether any additional upstream primitive is required for those decisions.
