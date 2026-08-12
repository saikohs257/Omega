# HF10 Information / Claim Court V1

Status: **draft constitution / pre-registered experiment gate**

This document formalizes the next TIAMAT boundary after the Pathbook and the diagnostic runner.
It does not promote TIAMAT to canonical runtime.

## One-line law

```text
A row is only eligible if its timing seat, information set, corpus snapshot, and registry snapshot are all frozen and content-addressed.
```

## Why HF10 exists

The earlier TIAMAT material repeatedly converges on the same unresolved scientific question:

- architecture is coherent,
- trajectory matters more than snapshot,
- recovery capacity is real,
- the state representation may be the contribution,
- but the system has **not** yet been falsified against simpler competitors.

The purpose of HF10 is to make that falsification legible.

## Core additions

### 1. InformationSet

The InformationSet is the legal observation contract for a row. It is stricter than a timing label.

```python
@dataclass(frozen=True)
class InformationSet:
    timing_seat: str
    observation_cutoff: datetime
    allowed_lookback: timedelta
    forbidden_future_window: timedelta
    label_offset: timedelta
    feature_snapshot_hash: str
    provenance_hash: str
    corpus_manifest_hash: str
    registry_snapshot_hash: str
    information_set_hash: str
```

Rules:

- `feature_timestamp <= observation_cutoff` at read time.
- Any future-contaminated dependency is rejected immediately.
- A row can be `INCOMPARABLE` even if its path seat is otherwise legal.

### 2. ClaimRegistry

The ClaimRegistry is append-only within a frozen registry version.
It records exactly what is being tested and what contradicts it.

```python
@dataclass(frozen=True)
class Claim:
    claim_id: str
    predictor: str
    path_seat: str | None
    timing_seat: str | None
    information_set_hash: str
    corpus_manifest_hash: str
    registry_snapshot_hash: str
    falsification_level: int
    status: Literal["PASS", "FAIL", "INCOMPARABLE", "ABSTAIN", "UNRESOLVED"]
    rationale: str
    contradictions: list[str]
    conventional_stack_hash: str | None
```

### 3. ConventionalBaselineV1

The TIAMAT continuation analysis already provides the conventional null candidate used for falsification:

- rolling 30d volatility
- recent drawdown (peak-to-current)
- 24h momentum
- volume spike versus 30d SMA

That baseline is now frozen as the pre-registered non-TIAMAT comparator for E1 and E2.

### 4. Five-state evidence taxonomy

- `PASS` — sufficient evidence supports the claim.
- `FAIL` — evidence points against the claim.
- `INCOMPARABLE` — wrong information set, wrong contract, or wrong authority.
- `ABSTAIN` — mechanism declines to produce a claim under the current gates.
- `UNRESOLVED` — the mechanism ran, but the evidence is genuinely contradictory.

`UNRESOLVED` is not `FAIL`.

## Registered experiments

### E1 — signal existence

Compare TIAMAT against trivial and conventional controls:

- uniform
- majority
- ConventionalBaselineV1

Question: does the TIAMAT representation contain signal beyond ordinary observed features?

### E2 — representation attribution

Compare the TIAMAT ablations against ConventionalBaselineV1:

- A = SimpleShock + RecoveryWeakness + LiveDeficit
- B = SimpleShock + RecoveryWeakness
- C = SimpleShock + LiveDeficit
- D = SimpleShock only
- E = Neural Kalman research comparator, if pre-registered

Question: which TIAMAT components actually matter?

### E3 — routing attribution

Compare:

- fixed TIAMAT
- routed TIAMAT
- BASE
- HOT
- PREC
- CHUG-like research variants

Question: does routing add value after the representation is fixed?

## Court order

HF10 runs the courts in this order:

1. Corpus freeze
2. InformationSet validation
3. Claim registration
4. Calibration court
5. Counterfactual court
6. Robustness court
7. Authority court
8. Promotion proposal to a new registry snapshot

## Hard gates

### L0–L2

- corpus and registry snapshots must be frozen
- no future-contaminated rows
- every claim must reference a valid InformationSet hash

### L3

- TIAMAT must beat the frozen null and ConventionalBaselineV1 under the pre-registered comparison policy

### L4

- TIAMAT ablations must survive the same information set and same metric contract

### L5

- routing must show local benefit beyond the fixed representation

### L6

- performance must hold across regime, path, timing seat, and perturbation checks

### L7

- operational cost and slippage assumptions must be pre-registered before the run

### L8

- only then can authority be proposed

## Failure-boundary language

A mechanism may be:

- `VALID`
- `SPARSE`
- `INCOMPARABLE`
- `INVALID`
- `UNTESTED`

This is stricter than a simple pass/fail split and is needed for the PROMOTE_TRUE_ENTER_STRONG style contradictions found in the research artifacts.

## Enforcement principle

HF10 does not resolve contradictions by mutation.
It records claims against frozen snapshots.
A new claim requires a new registry version.
A new registry version requires a new hash.

No experiment may promote its own conclusion.
