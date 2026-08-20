# SENATE / BLACKADDER / SEAM / HINGE CONTRACT V1

Date: 2026-08-20
Status: architecture contract / archaeology consolidation

## Senate

### Purpose

The Senate is the decision institution. It is explicitly not a monarchy.

A seat may contribute evidence without acquiring command authority.

### Seat classes

- `PROMOTABLE`: eligible for policy contribution under current gate rules.
- `DIAGNOSTIC_ONLY`: produces useful evidence but cannot steer.
- `SHADOW`: executes/evaluates without authority to mutate policy.
- `ANNOTATION_ONLY`: local description/routing aid; never a vote.
- `RESERVE`: structurally known but not yet promoted.

### Current concrete spine

Known active seats from the recovered decision-friction/senate work:

- `B1_entry`
- `flip_risk_24h`
- `flip_alarm_6h`
- `in_episode_owner_v3`
- `post_exit_owner_v3`
- `family_gate`

Known excluded / non-core seats:

- `seam_confidence` — annotation sidecar
- `seam_watch_pressure` — annotation sidecar
- `seam_watch_pressure_bear_probe` — annotation sidecar
- `novelty_guard` — quality/reserve guard

These classifications are architecture memory and must be verified against the canonical senate implementation before being treated as executable policy.

## Blackadder

### Purpose

Blackadder is the controller's self-audit / proprioception layer.

It asks whether the ornate controller decision materially departs from a simpler legal spine.

Key concepts:

```text
full path
stripped spine
spine confidence
full path confidence
divergence
path tax
review priority score
proposed reroute
trust discount
```

### Constitutional rule

```text
controller divergence != evidence that the ornate path is better
controller divergence == evidence that the controller is under strain
```

Therefore Blackadder is primarily a trust-calibration instrument.

## Deciding non-vote

The recovered conceptual role of Blackadder/Senate includes a deciding mechanism that does not become a king.

The mechanism should be implemented as:

1. evidence tally / seat state,
2. confidence / support accounting,
3. constitutional eligibility gates,
4. deciding resolution only inside the legal scope,
5. immutable audit record.

No single seat may acquire global authority merely because it wins one decision.

## Seam

### Current role

Seam is a local transition/attention surface.

It may encode:

- local boundary position
- local width
- seam distance
- drift
- family gating
- watch-band pressure

It is not a universal class predictor.

It may route attention or annotation to a narrow region without becoming a global voting seat.

### Known regime roles

Recovered master-state semantics identify:

- `seam_watch_pressure = ACTIVE_ANNOTATION_BULL_ONLY`
- `seam_watch_pressure_bear_probe = ACTIVE_ANNOTATION_BEAR_STABILITY_PROBE`
- `seam_confidence = ACTIVE_SIDECAR`

Older broad/static seam doctrines are historical unless revalidated.

## Hinge

Hinge is a structural fragility / prior-state lane.

The recovered architecture treats Hinge as contextual information about where episode structure is fragile. It is not automatically a universal predictor and must remain distinct from Domino/UTV timing sensors.

## Promotion doctrine

A Seam/Hinge/Blackadder/Senate component must not be promoted because:

- it looks novel,
- it is interpretable,
- it correlates in-sample,
- it is useful in one regime,
- another component agrees with it.

Promotion requires a bounded contract, out-of-sample evidence, provenance, failure analysis, and authority classification.
