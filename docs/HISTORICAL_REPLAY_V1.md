# Historical Replay V1

## Purpose

Determine whether Omega's causal state trajectory contains useful information before known historical outcomes.

This is a research harness. It does not change production Omega or TIAMAT.

## Causal boundary

At timestamp `t`, the replay model may use only observations with timestamps `<= t`.

Outcome labels are generated separately from future bars. They are evaluator-side ground truth and are never passed into the causal observation object.

## Initial data contract

CSV columns:

```text
timestamp,close,volume(optional)
```

Timestamps must be strictly increasing. Close must be finite and positive.

## Outcome protocol

`OutcomeSpec` is frozen before a run. It contains:

- `horizon`: number of future bars inspected
- `drawdown`: fractional decline required for a positive crash label
- optional recovery settings

Do not tune the outcome rule after inspecting Omega results. Change it only by creating a new versioned specification.

## Replay artifacts

Each row has two distinct objects:

```text
CausalObservation  -> what Omega is allowed to see
OutcomeLabel       -> what the evaluator knows afterward
```

This separation is intentional and test-enforced.

## First empirical pass

Start with Bitcoin because the data is readily obtainable and the history contains obvious known stress episodes. Include matched non-crash periods, not only crashes.

Minimum event classes:

1. major crash
2. ordinary correction
3. continuation without crash
4. recovery after drawdown

The first run is diagnostic. Do not tune thresholds or add mechanisms from its results.

## Next adapter

The next research change should connect `CausalObservation` to an Omega/TIAMAT shadow-state adapter and emit an event-aligned disagreement ledger. The historical data provider remains outside this package so the experiment can be reproduced from a frozen CSV.
