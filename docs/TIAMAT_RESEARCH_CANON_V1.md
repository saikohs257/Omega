# TIAMAT Research Canon V1

**Status:** research architecture / non-runtime authority
**Purpose:** reconcile the Pathbook, calibration, authority, current, false-watch, and proof-mode research into one explicit layer model before native-corpus execution.

## 1. Governing law

TIAMAT owns the Pathbook. The Pathbook decides which prediction is legal. Heads do not receive global authority merely because they score well.

This document is a research contract, not a runtime authority declaration.

## 2. Layer order

```text
SOURCE / CORPUS
    -> NATIVE ROUTE EXTRACTION
    -> PATHBOOK SEATS
    -> HEAD-LOCAL RAW SCORES
    -> TIMING / CONTINUATION SEATS
    -> CALIBRATION COURT
    -> AUTHORITY / CONFLICT COURT
    -> FALSIFICATION COURT
    -> DIAGNOSTIC REPORT
```

No layer may silently perform the job of a later layer.

## 3. Path and timing separation

`start_transition_path` and `topology_path` are independent seats.

Known topology seats include `0_to_4`, `2_to_4`, `3_to_4`, and `4_to_4`.

`4_to_4` must not be fabricated as a legacy doorway label when the source only establishes topology.

Timing seats are distinct:

- `ActiveBurden`: runtime-time surface burden.
- `ExitBridgeDeficit`: `ActiveBurden` sampled at episode end.
- `PriorCarryDeficit[t]`: prior episode bridge shifted forward.

No prior/carry/exit field is trusted by name alone; timing construction and provenance are required.

## 4. Head registry boundary

The current research heads are scoped, not global:

- H0 / `0_to_4` / FalseCalmIgnition
- H2 / `2_to_4` / ResetDragRelease
- H3 / `3_to_4` / RecoveryInversion
- H4 / `4_to_4` / CeilingTrap
- ExitBridge
- Carry

Candidate transition classes outside these heads remain candidate seats until a promotion court explicitly promotes them. Observed transition frequency is not a promotion rule.

## 5. Formula/calibration separation

Head formulas are raw structural scores. Calibration is a later layer.

```text
head formula -> raw score -> calibration -> probability
```

Calibration must never rewrite the head formula.

Small-support lane heads are research relative-risk outputs unless their probability semantics are independently established. Timing heads with sufficient support may enter probability calibration under the frozen metric contract.

## 6. Current / conductance law

Amplitude is not current. Current is not globally authoritative.

The surviving research interpretation is:

```text
current = pressure movement through an allowed/conducting route
```

State-conditioned current may be evaluated only after route permission / conductance is established. Global current promotion is blocked.

## 7. False-watch / authority law

False-watch is an authority interpretation grammar, not a standalone predictor.

Allowed research outcomes include conversion-confirmed, false-watch escape-confirmed, rebound/recycle casebook states, unresolved/no-authority, and conflict/no-authority states.

High-high conflict must remain no-authority rather than being resolved by an arbitrary winner.

Alert-budget and causal-order gates remain part of any future promotion experiment.

## 8. Forbidden promotion shortcuts

The following are not sufficient for promotion:

- one strong AUC
- one fitted calibrator
- one calendar/regime split
- raw transition frequency
- a field name implying prior/exit/carry semantics
- normalized scores masquerading as probabilities
- same-spine threshold tuning
- mixed-source runtime unions
- retrospective episode-end information leaking into timestamp-t estimates

## 9. Falsification requirements

Every candidate family must be compared against controls and a simple null. The research record must preserve failure as first-class evidence.

The current external research record identifies head-to-head comparison against simple state-space/Kalman and null baselines as the decisive unresolved test. This canon therefore treats `winner` as undefined until the diagnostic and falsification gates pass.

## 10. Independence requirement

The strongest remaining scientific gate is an independent canonical feature rebuild / native route extraction on a frozen spine. Existing mixed-source unions are inspection artifacts and must not become runtime authority.

## 11. Artifact requirement

Every diagnostic run must use the existing experiment identity and sealed calibration-bundle path. The diagnostic runner must not have a special real-corpus writer.

The bundle must preserve:

- calibration report
- reliability bins for every comparable predictor
- metric distributions
- explicit incomparable records with reasons
- bundle manifest and cross-artifact hashes

## 12. M7 and historical controls

M7 is comparable only after its declared probability mechanism is verified. A normalized score is not automatically a probability adapter.

The historical control is comparable only after it passes the same probability contract or is explicitly recorded as `INCOMPARABLE`.

No synthetic adapter may be introduced merely to improve tournament coverage.

## 13. Execution gates

### Gate A — native route extraction

Produce the canonical all-head hourly table with path and timing seats preserved.

### Gate B — controls-only diagnostic

Run uniform and majority controls, plus historical only if its probability contract is verified. Produce a sealed artifact and force `HOLD`.

### Gate C — M0-M7 diagnostic

Run all available candidates without selection. Require null-floor, cross-model spread, and reliability behavior checks.

### Gate D — calibration report

Freeze the diagnostic decision and rationale as an artifact.

### Gate E — selector

Selection is permitted only after Gate D returns `PROCEED`.

### Gate F — falsification

The selected result must still beat the null/control references on predeclared metrics and confidence intervals. A selector winner is not a scientific winner by itself.

## 14. Current status

```text
ERK canonicalization                 GREEN
Experiment identity                  GREEN
Probability / metric contracts       GREEN
Sealed calibration artifacts         GREEN
Native Pathbook route extractor      SCAFFOLD / RESEARCH
Independent real corpus              NOT YET CONNECTED
M7 probability semantics             UNVERIFIED
Historical probability adapter       UNVERIFIED
Runtime authority                    BLOCKED
Probability authority                BLOCKED
Global burden authority              BLOCKED
```

## 15. Enhancement: Evidence Ledger

Every promoted research claim should carry five fields:

```text
claim_id
source_artifacts
source_hashes
gate_status
authority_status
```

This prevents a later handoff from turning a research survivor into a runtime fact simply because its name appears in a registry.

## 16. Final rule

```text
The Pathbook may define what is legal to test.
The evidence court decides what survives.
The calibration court decides how probabilities are represented.
The authority court decides whether a research result may be interpreted.
No single head, field, score, or artifact owns the whole system.
```
