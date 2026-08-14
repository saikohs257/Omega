# TIAMAT LiveDeficit Upstream Research

## Status
Candidate reconstruction: **ABODY-1**. Not yet canonical.

The recovered producer for `entry_path` is:

```python
prev_ld = LiveDeficit.shift(1)

if prev_ld <= 0.70:
    entry_path = "0_to_4"
elif prev_ld <= 0.85:
    entry_path = "2_to_4"
else:
    entry_path = "3_to_4"
```

This makes `entry_path` a discretization of previous-hour `LiveDeficit`, not an independent hidden state.

## ABODY-1 candidate LiveDeficit recursion

Recovered from prior project archaeology:

```text
logit(LiveDeficit[t]) =
    0.952 * logit(LiveDeficit[t-1])
  + 0.367 * max(0, -ret_1h[t] * 100)
  - 0.232 * max(0,  ret_1h[t] * 100)
  + 0.057 * SimpleShock[t]
  + 2.431 * max(0, SimpleShock[t] - 0.70)
  - 0.074 * robust24h_downside[t]
  - 0.068
```

with `LiveDeficit[t] = sigmoid(logit_value)`.

The exact historical `build_live_recovery_deficit()` implementation and exact `robust24h_downside()` helper were not found in the recovered artifact corpus, so the formula remains a candidate reconstruction.

## Native 43,848-row test

Using the exact 2020–2024 Layer-1 spine and a provisional downside helper:

- Rows evaluated: **42,477**
- Pearson correlation vs native `LiveDeficit`: **0.9964**
- Spearman correlation: **0.9957**
- MAE: **0.0102**
- RMSE: **0.0191**
- Candidate-vs-entry-path-active diagnostic AUC: **0.9725**

These results are unusually close and make the upstream LiveDeficit recursion the strongest current candidate for the shared-body generator.

## Important interpretation

This result does **not** prove the exact original generator. The provisional `robust24h_downside` helper is not yet recovered exactly, and the comparison is against the saved native output.

However, it changes the research priority:

1. Recover the exact `robust24h_downside` definition.
2. Replay ABODY-1 recursively from the true initial condition, not by seeding each row with native `LiveDeficit[t-1]`.
3. Require full-series agreement, not correlation alone.
4. Then test whether this recovered LiveDeficit naturally reproduces the entry-path thresholds and downstream H0/H2/H3/ExitBridge behavior.

## Architectural implication

The current evidence favors:

```text
upstream forcing / recovery dynamics
          ↓
     LiveDeficit[t]
          ↓
   previous-hour LD bucket
          ↓
    entry_path 0/2/3
          ↓
      active episode
          ↓
   topology-specific head
```

This is a more constrained and testable architecture than a free-standing ActiveBurden scalar.

## Do not do yet

- Do not rename ABODY-1 to canonical ActiveBurden.
- Do not freeze the 0.6/0.4 hazard+burden projection.
- Do not tune H3 merely to exceed an AUC target.
- Do not promote the 4→4 ~0.34 threshold without fresh 4→4 evidence.
