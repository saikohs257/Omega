# TIAMAT Interface Boundary V1

Status: research note / non-runtime authority.

## Core claim

Historical TIAMAT is not failing because its internal diagnostic logic is meaningless. It is failing the modern comparison pipeline because it never declared or validated a probability interface.

That matters because a bounded diagnostic score is not automatically a calibrated probability.

## Two distinct contracts

### 1. Structural diagnostic contract

This is the historical TIAMAT shape:

```text
telemetry -> latent state reconstruction -> hazard / mode / guard / hysteresis -> diagnostic artifact
```

Outputs in this contract can be very useful while still being non-probabilistic.

### 2. Probability contract

This is the tournament shape:

```text
telemetry -> predictor -> p(event | features) -> validated probability vector -> metrics / calibration
```

A predictor must explicitly satisfy all of the following:

- return a full probability distribution over the declared state space;
- sum to 1 within tolerance;
- stay finite and non-negative;
- preserve the declared state labels exactly;
- be recorded as a probability-capable predictor, not assumed to be one.

## Why this matters for TIAMAT

If historical TIAMAT only emits `hazard_score`, `mode`, `guard_reason`, or similar diagnostic values, then the correct scientific classification is:

- `INCOMPARABLE` for probability tournaments,
- not `PASS`,
- not `FAIL`,
- and not “probably probabilistic.”

That preserves the historical artifact without mutating it into a new model.

## Recommended repository rule

Whenever a TIAMAT family is evaluated against the canonical runner, the report should preserve three separate fields:

- `status`: `PASS`, `FAIL`, `INCOMPARABLE`, `ABSTAIN`, or `UNRESOLVED`
- `rationale`: why the status was assigned
- `interface_type`: `diagnostic` or `probability`

That separation keeps the evidence readable and prevents a wrapper from being mistaken for the original mechanism.

## Minimal adapter rule

If a future family wants to enter the probability tournament, it should not silently reuse a diagnostic score.
It should provide a declared adapter such as:

```python
class ProbabilityAdapter(Protocol):
    def __call__(self, row) -> Mapping[str, float]: ...
```

The adapter becomes part of the model identity and must be versioned and tested separately.

## Bottom line

Historical TIAMAT remains important because it may encode real structural state logic.
Its missing piece is not “a better score”; its missing piece is a declared, validated probability interface.
