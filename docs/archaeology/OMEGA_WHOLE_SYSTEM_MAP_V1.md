# OMEGA Whole-System Map v1

**Status:** archaeological consolidation / non-authoritative map  
**Date:** 2026-08-19  
**Rule:** recovered facts are separated from hypotheses; this document does not promote uncertain genealogy into runtime authority.

## 1. Current whole-system inventory

### Substrate and observation
- Raw market/episode observations.
- Hourly Layer 1 spine and episode-level fields.
- Daily derived features and rolling context.

### Episode and persistence machinery
- Run Tracker.
- Episode type / age / transition context.
- Carry / unresolved burden across episodes.
- Entry and exit context.

### Structural machinery
- **Hinge:** structural tension / fragility composite; not a universal outcome predictor.
- **Seam:** local transition-boundary / ambiguity geometry; currently best treated as routing/annotation rather than a universal predictor.

### Hazard / response machinery
- Hazard channels.
- `haz_activation_raw_v1` as an episode-level field.
- Recovery / repair / persistence / propagation / re-entry arms.
- Important data gap: `haz_recovery_obstruction_raw_unresolved` is entirely null in the 453-row episode panel; obstruction analysis therefore requires another source.

### Decision / governance
- **Senate:** evidence/authority fusion with seat eligibility, promotion/demotion, diagnostic-only seats, and escalation constraints.
- **Blackadder:** decision-friction / path-vs-spine comparison layer. The recovered implementation runs after `fuse_votes()` and is not a market-allow authority. It compares full-path and stripped-spine actions/confidence and measures divergence.

### Topology / inverse-state machinery
- **TESSERACT / Atlas:** topology and legal-transition representation.
- **TESSERACT_CIRCUIT:** executable circuit formulation of topology/transition pressure.
- **TIAMAT:** deterministic hidden-state reconstruction / controller archaeology runtime.
- **BentAxis:** evidence/index/compression/proof/capsule substrate around the structural runtime.

### Higher-order governance / coordination
- **Oracle:** constitutional decision/governance doctrine and higher-level empirical architecture.
- **Court:** governance/audit layer.
- **Collective / Colony:** distributed inference / coordination machinery.
- **ERK:** known subsystem; exact genealogy/function remains under archaeological review.

## 2. Confirmed architectural principles

1. Measurement and authority are distinct.
2. Diagnostic usefulness does not automatically imply policy authority.
3. Local boundary geometry can be useful for routing without being promoted to a universal predictor.
4. The full decision path can be audited against a stripped evidentiary spine.
5. Decision machinery can be evaluated for friction/strain without treating that strain as predictive alpha.
6. Canonical runtime behavior must be supported by implementation and replay/holdout evidence; speculative equations remain outside authority.
7. Sequence, path, carry, and response state can matter differently; universal feature promotion is unsafe without path-stratified evidence.

## 3. Empirical results recovered during archaeology

### Carry × activation
A replicated 2026-04-02 analysis reported:
- carry on severity AUC ≈ 0.702;
- carry + activation AUC ≈ 0.759;
- carry + path + activation AUC ≈ 0.808;
- activation coefficient negative after controlling for carry;
- high-carry/low-activation had the highest reported severity rate;
- activation added essentially nothing for onset but materially improved severity discrimination.

Interpretation retained as an empirical hypothesis/working model: activation behaves more like response/defense engagement than a simple hazard-amplifying signal.

### Path asymmetry
The same analysis reported materially different severity behavior for paths `2_to_4` and `3_to_4`, implying path-stratified policy curves may be required. This is a tested finding, not yet a canonical runtime rule.

### Re-entry / propagation redundancy
`haz_reentry_raw_v1` and `haz_propagation_raw_v1` were reported at correlation `r = 0.865`; treat them as potentially near-alias mechanisms until independently separated.

### Seam / Hinge negative knowledge
Seam and Hinge should not be silently promoted into global predictors merely because they remain useful for local routing/annotation/structural attention.

## 4. Blackadder archaeological status

### Confirmed implementation facts
- Blackadder is implemented as a decision-friction seat/layer.
- The implementation compares full-path and stripped-spine actions.
- It compares full-path and spine confidence.
- Divergence contributes to review/friction scoring.
- The integration point is after the Senate vote fusion result.
- It is quality/support oriented and not itself a market-allow authority in the recovered implementation.

### Historical hypothesis
A separate user-memory/archaeology line suggests the original Blackadder concept was a **non-voting deciding mechanism** intended to resolve evidentiary ties without becoming sovereign. The exact original implementation and whether this was the direct ancestor of the later Decision Friction implementation remain unresolved.

## 5. Senate archaeological status

### Concrete spine recovered
Active seats include:
- `B1_entry`
- `flip_risk_24h`
- `flip_alarm_6h`
- `in_episode_owner_v3`
- `post_exit_owner_v3`
- `family_gate`

Excluded/diagnostic seats included Seam annotation seats and a reserve `novelty_guard` seat.

The architecture distinguishes active policy authority from diagnostic/annotation capability.

## 6. Unresolved genealogy

The following names are known but should not be forced into a single lineage without artifact recovery:

- CHUG
- HF8
- HF9
- DIC
- BAGE
- CARR
- Attack
- Release
- Capacity
- Exit Latch
- ERK

Open possibilities include independent mechanisms, generations, feature projections, sidecars, routers, abandoned experiments, or later recombinations.

## 7. Current architectural hypothesis

```text
Observation
    -> episode/state reconstruction
    -> structural + response + transition measurements
    -> hidden-state / topology reasoning
    -> Collective / Senate governance
    -> final decision
    -> Blackadder decision-machinery audit
    -> Oracle / Court constitutional handling
```

This is a working map, not a claim that every historical subsystem directly occupied every arrow.

## 8. Provenance discipline

Every future archaeology artifact should be classified as one of:

- recovered implementation
- reproduced test result
- tested but not promoted
- diagnostic-only
- annotation/routing-only
- rejected
- superseded
- hypothesis / unresolved genealogy

No historical result should acquire production authority merely by being deposited in the repository.
