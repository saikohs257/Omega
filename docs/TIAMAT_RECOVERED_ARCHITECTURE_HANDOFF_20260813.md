# TIAMAT Recovered Architecture Handoff

**Date:** 2026-08-13  
**Purpose:** Preserve the recovered TIAMAT architecture, evidence, terminology, experiments, and current unknowns so future work does not have to reconstruct the history from chat.

> This document separates **recovered/source-supported facts** from **current hypotheses and open verification work**. No item marked as a hypothesis should be promoted to runtime authority without a court.

---

## 1. Executive conclusion

TIAMAT should not be treated as four generic predictors sharing one global feature space.

The recovered work describes TIAMAT as:

```text
shared causal substrate
        |
        +-- topology-native path heads
        |
        +-- episode-boundary timing head
        |
        +-- shifted continuation-memory seat
```

The four path heads are scoped to specific episode transitions:

- `0_to_4` -> **FalseCalmIgnition**
- `2_to_4` -> **ResetDragRelease**
- `3_to_4` -> **RecoveryInversion**
- `4_to_4` -> **CeilingTrap** (currently a scout/proxy because literal 4_to_4 rows are absent from the current hourly panel)

The timing seats are:

- **ExitBridgeDeficit** -> episode-end bridge / next-trigger timing
- **PriorCarryDeficit** -> exact shifted previous ExitBridge state used for continuation memory

The strongest architectural lesson is that **scope is part of the meaning of a head**. A head is not merely a classifier assigned a different weight vector; it is a readout for a particular location/transition in the state topology.

---

## 2. Native lane map

| Seat | Native scope | Recovered name | Current interpretation |
|---|---|---|---|
| Head 0 | `0_to_4` | FalseCalmIgnition | spark / false-calm ignition lane |
| Head 2 | `2_to_4` | ResetDragRelease | burden corridor / drag / stuck / reset-release lane |
| Head 3 | `3_to_4` | RecoveryInversion | phantom clear / recovery inversion lane |
| Head 4 | `4_to_4` | CeilingTrap | no-escape / critical-hazard self-loop proxy |
| Exit | episode boundary | ExitBridgeDeficit | next-trigger / re-entry timing |
| Carry | shifted episode boundary | PriorCarryDeficit | continuation memory |

Recovered handoff terminology explicitly says:

```text
0_to_4 = FalseCalmIgnition / latent fuel / spark lane
2_to_4 = burden corridor / drag / stuck / reset-release lane
3_to_4 = recovery inversion / phantom clear lane
4_to_4 = ceiling trap / no-escape proxy lane
```

Literal `4_to_4` rows were absent in the current hourly panel, so the 4_to_4 seat used a critical-hazard self-loop proxy and must remain **scout-only until a native aligned extract is recovered**.

---

## 3. What the heads actually do

### Head 0 — FalseCalmIgnition (`0_to_4`)

This is an **entry-path gate**, not a universal hazard predictor.

Recovered controller behavior:

```text
if hazard_score >= 0.92:
    trapped
else:
    mixed
```

Recovered population in one reconstruction: 58 mixed, 5 trapped, 0 phasic.

Working semantic:

> Given a 0_to_4 arrival, is the arrival already sufficiently hazardous to be treated as trapped, or is it a mixed/spark state?

Recovered lane description also calls this the **shock-led / latent-fuel / spark** lane.

Starter family concept recovered from prior work:

```text
shock + false-calm fuel + range/volume expansion
```

The starter formula is not canonical authority.

---

### Head 2 — ResetDragRelease (`2_to_4`)

This is an entry gate centered on accumulated burden and hazard.

Recovered compound gate:

```text
(hazard_score >= 0.88 AND LiveDeficit >= 0.90)
OR
(hazard_score >= 0.95)
```

This replaced an older shock-only trapped rule whose recall was inadequate. The recovered notes report approximately 65% trapped recall for the compound rule.

Working semantic:

> Has a 2_to_4 arrival accumulated enough hazard and burden to represent a trapped/dragged state rather than a recoverable reset-release?

Lane owner:

```text
ActiveBurden-led
+ recovery failure
+ drawdown stress/scar
```

This is the strongest direct historical example of the `A x B` idea: hazard and burden were explicitly combined in the native gate.

---

### Head 3 — RecoveryInversion (`3_to_4`)

This is the most important head to preserve correctly.

It is **not** simply a generic hazard classifier.

Recovered hard trapped boundary:

```text
if hazard_score >= 0.966:
    trapped
```

Otherwise the controller evaluates a phasic/acute score involving:

- current shock
- recent hazard peak/history
- 5-day volume expansion
- recent episode-start tempo
- a burst/tempo override

The recovered scoring gives shock unusually strong influence and includes an acceleration/tempo component.

Working semantic:

> Did recovery merely *look* like it happened because the immediate shock faded while the underlying burden remained unresolved?

The strongest recovered native anchor is approximately:

```text
LiveDeficit - SimpleShock_0_4h_max
AUC ~ 0.8929
```

This is the basis for the **RecoveryInversion / phantom-clear** interpretation.

Important: a recent proxy experiment produced a spectacular `BURDEN x HAZARD` H3 result, but that effect **did not survive** when the actual native 43,848-row Layer-1 data were used and final-label leakage was removed. Therefore the proxy result must not be treated as the native H3 mechanism.

---

### Head 4 — CeilingTrap (`4_to_4`)

Recovered semantic:

> critical self-loop / ceiling / no-escape condition.

Native aligned `4_to_4` hourly rows were absent from the current panel. The historical work therefore used a critical-hazard self-loop proxy.

Recovered lane owner:

```text
absolute burden
+ hazard shelf
+ persistence
```

A previous scout produced very strong performance, but this is explicitly **not native authority** until the missing 4_to_4 aligned extract is recovered.

Do not use the scout AUC as proof that H4 is solved.

---

## 4. ExitBridgeDeficit

This is not another ordinary path head.

Recovered definition:

```text
arm_exit_live_deficit = ExitBridgeDeficit
```

Meaning:

> current episode exit-bridge state, known at `episode_end_time`.

Owner:

- next-trigger / re-entry timing labels
- `next_trigger_6h`
- `next_trigger_24h`
- `next_trigger_48h`

Recovered AUCs were approximately:

```text
6h   ~0.742
24h  ~0.713
48h  ~0.690
```

This state must be sampled at the **episode end boundary**. It must not be confused with current runtime burden or shifted prior carry.

---

## 5. PriorCarryDeficit

The correct prior carry is a pure episode-order shift:

```text
PriorCarryDeficit[t] = ExitBridgeDeficit[t-1]
```

The reconstruction matched shipped lineage for **452/452** prior-carry comparisons.

Dangerous ambiguous names that must not be trusted by name alone:

- `prev_exit_live_deficit`
- `prior_exit_live_deficit`
- `prior_exit_live`
- `prev_exit_live`

Timing lineage, not the field name, determines whether a value is current boundary state or shifted prior carry.

---

## 6. ActiveBurden is not ExitBridgeDeficit

Recovered distinction:

```text
ActiveBurden = LiveDeficit / load
```

It means current runtime burden.

It is **not**:

- ExitBridgeDeficit
- PriorCarryDeficit

A major failed reconstruction tried to force one scalar to reproduce all of:

- hourly burden shape
- ExitBridge next-trigger timing
- PriorCarry continuation memory
- 2_to_4 burden corridor
- 3_to_4 recovery inversion
- 4_to_4 ceiling trap

It could not do all jobs simultaneously.

This is strong evidence against collapsing TIAMAT into a single universal burden scalar.

---

## 7. Continuation lanes

The recovered timing work separates short and long continuation.

### Short non-worsened continuation: 12–24h

Owner:

```text
PriorCarryDeficit + SimpleShock_0_4h_max
```

Hazard is audit-only / a small optional complement.

Recovered AUCs were approximately:

```text
shock alone        ~0.709
shock + hazard     ~0.733
```

### Long non-worsened continuation: >24h

Owner:

```text
PriorCarryDeficit + hazard_raw_0_4h_max
```

Shock is the complement.

Recovered best AUC was approximately **0.9356** for carry + hazard + shock.

Important methodological rule:

> Hazard being strong at the short-vs-long duration boundary does **not** make hazard the owner of the short-continuation lane.

The old work explicitly froze the short lane as carry + shock, with hazard audit-only/small complement.

---

## 8. Why head scoping matters

The same burden/hazard observation means different things depending on how the episode arrived at the state.

The recovered structural description treats the system as:

```text
body   = shared burden substrate
ridges = episode paths
valleys = failure modes
heads  = lane-native readouts
```

Therefore:

```text
H0 cannot be interpreted as H2.
H2 cannot be interpreted as H3.
H3 cannot be interpreted as H4.
ExitBridge is not a path head.
PriorCarry is not current burden.
```

The correct question is not:

> Which universal feature predicts the head?

It is:

> Which evidence is meaningful **given that this head is scoped to this particular transition or timing seat?**

---

## 9. The A x B discovery

The family-interaction idea was useful, but the recovered native architecture shows that the interaction should be interpreted as **lane-specific mechanism**, not arbitrary feature multiplication.

Examples:

- H2 already contains a native **hazard x burden** style compound gate.
- H3 is better represented by **burden remaining after immediate shock fades**, plus hazard/recovery context.
- Short continuation is **carry x shock** in the sense of two complementary state sources.
- Long continuation is **carry x hazard**, with shock as complement.

Therefore future experiments should test:

```text
A
B
A+B
A x B
A x B x C
```

but only **inside the legal scope of the seat**.

Do not pool all heads and search for a universal winning interaction.

---

## 10. Metrics and selection rules

AUC alone is insufficient.

For family selection, preserve at least:

- AUC / discrimination
- Brier score / probability quality
- calibration
- interaction gain
- leave-one-year-out stability
- complexity
- lane scope

Do not invent arbitrary AUC/Brier weights merely to force a single winner.

Prefer a Pareto view or explicit multi-criterion court.

An `A x B` candidate is interesting only if it adds information beyond A or B and survives held-out evaluation.

---

## 11. Native 43,848-row examination

The native file recovered in this work is:

`layer1_structured_hazard_arm_timeseries(15).csv`

It contains **43,848 rows and 15 columns** and includes native Layer-1 fields including:

- `SimpleShock`
- `LiveDeficit`
- `RecoveryWeakness_v1`
- `recovery_gate`
- `entry_path`
- `episode_age_h`
- `duration_bucket`
- `regime_30d`
- `episode_type`
- `hazard_raw`
- `hazard_score`
- `hazard_bucket`
- `Crash72`

The native panel contains approximately **4,026 active/eligible rows** in the current causal-only examination.

### Leakage rule

`episode_type` and `duration_bucket` are final episode labels and must not be allowed to act as ordinary predictive inputs in causal mechanism discovery.

When those were removed from the native family tournament, the spectacular proxy H3 `BURDEN x HAZARD` effect disappeared.

That disappearance is a **methodological success**, not a failure: it prevented a contaminated proxy relationship from being promoted as native TIAMAT behavior.

---

## 12. Native causal-only tournament findings so far

Current leakage-clean native family results:

- **H0:** no meaningful stable interaction winner yet.
- **H2:** `AGE + RECOVERY` showed about +0.0167 mean OOS AUC gain but only 1/5 positive years; `BURDEN + HAZARD` showed about +0.0065 mean gain and 4/5 positive years, but is not strong enough to declare the mechanism.
- **H3:** `AGE + HAZARD` showed about +0.0540 mean OOS gain but only 1/5 positive years; `HAZARD + RECOVERY` about +0.0284, also only 1/5 positive years.
- **H4:** `AGE + SHOCK` showed about +0.0085 mean OOS gain and was positive in 4/5 years; this is currently the most stable interaction candidate, but H4 itself remains a proxy/scout until native 4_to_4 rows are recovered.

These statistical results do **not** override the recovered deterministic path logic. They are evidence for/against candidate reconstructions.

---

## 13. Historical proxy experiment: preserve but do not confuse with native

A proxy historical panel previously produced a striking H3 result:

```text
BURDEN x HAZARD
AUC gain ~+0.242
Brier improved substantially
positive OOS gain in all five years
```

That result was useful as a hypothesis generator.

It **did not survive** the native 43,848-row leakage-clean test.

Therefore:

```text
PROXY RESULT = hypothesis only
NATIVE RESULT = governing evidence for reconstruction
```

Never merge the two datasets or quote the proxy result as native TIAMAT performance.

---

## 14. Recovered starter formulas — NOT authority

The historical handoff contained starter family formulas roughly of this form:

```text
Head 0:
0.60 * shock
+ 0.25 * false_calm_fuel
+ 0.15 * range_pop

Head 2:
0.55 * ActiveBurden
+ 0.25 * recovery_failure
+ 0.20 * drawdown_stress

Head 3:
0.60 * max(ActiveBurden - shock, 0)
+ 0.25 * hazard_shelf
+ 0.15 * recovery_failure

Head 4:
0.50 * ActiveBurden
+ 0.35 * hazard_shelf
+ 0.15 * recovery_failure

ExitBridge:
0.45 * ActiveBurden
+ 0.30 * hazard_shelf
+ 0.25 * recovery_failure
```

These were explicitly starter candidates. They are not canonical TIAMAT authority and must be tested through the Promotion Court.

---

## 15. What failed / what not to repeat

### Do not build one scalar `LiveDeficit_v2`

The recovered handoff explicitly says not to force all lanes and timing jobs into one scalar.

### Do not use global path routing as a universal predictor

Path is meaningful as a scope/router but was demoted as a universal predictor.

### Do not use prior-duration memory as a universal seat

It was demoted in the recovered doctrine.

### Do not trust field names

Timing lineage is authoritative. Ambiguous `prior_*` fields can be contaminated with current-row values.

### Do not promote H4 from its scout AUC

Native literal 4_to_4 rows were absent in the current hourly panel.

### Do not interpret proxy A x B results as native mechanisms

The H3 proxy result failed the native leakage-clean test.

### Do not use global pooling to discover head semantics

The heads are topology-native and should be sampled only inside their legal scopes.

---

## 16. Promotion Court doctrine

The recovered handoff gives the correct next verification target:

> **Run TIAMAT Promotion Court V1 head-by-head on six seats:**
> `0_to_4`, `2_to_4`, `3_to_4`, `4_to_4`, `ExitBridge`, `PriorCarry`.

Required panels recovered in the handoff:

- 36-row V4.1F holdout
- 73-row ledger
- 453 episode boundary panel
- Step174 regenerated short child
- available 4_to_4 aligned extract/scout

Required scope rules:

1. Build shared causal substrate from hourly OHLCV/OI/IV/Layer1 fields.
2. Build episode table with start/end, path, duration, labels.
3. Generate four path heads and two timing heads.
4. Sample path heads only inside native path scope.
5. Sample ExitBridge at episode end index.
6. Shift ExitBridge to PriorCarry.
7. Run Promotion Court per head.
8. Reject global claims.
9. Runtime authority remains false until promotion.

The historical handoff explicitly says:

```text
No head promotes globally.
```

---

## 17. Current best understanding of the state machine

```text
                    SHARED CAUSAL SUBSTRATE
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
          0_to_4            2_to_4            3_to_4
          spark             burden            recovery
          ignition          drag              inversion
             |                |                |
             +----------------+----------------+
                              |
                              v
                           4_to_4
                         ceiling trap
                         (scout until
                       native rows exist)
                              |
                              v
                       EPISODE BOUNDARY
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             ExitBridgeDeficit   PriorCarryDeficit
             current boundary     previous boundary
                    |                   |
                    v                   v
             next-trigger        continuation
              timing              memory
```

This architecture explains why the system repeatedly resisted a single universal head scope.

---

## 18. Deeper architectural hypothesis

A later TIAMAT inference-core handoff reframed the system more generally as:

```text
Observations
    -> Constraints
    -> Competing Explanations
    -> Evaluation Operator
    -> Revision Policy
    -> Emergent Observables
```

Candidate emergent properties included:

- memory
- pressure
- recovery
- authority
- trust
- maturity
- state
- prediction
- ambiguity
- consensus
- quarantine
- promotion

This is a **working hypothesis**, not a replacement for the recovered concrete TIAMAT state machine.

The handoff specifically instructed future work to search for deeper conserved quantities, optimization/evaluation operators, control-theoretic and information-theoretic reductions, and to falsify proposed primitives before accepting them.

---

## 19. What remains unanswered

### A. Native H0 reconstruction

Verify that the recovered shock/fuel/range structure reproduces the actual `0_to_4` behavior without leakage.

### B. Native H2 reconstruction

Verify the hazard + ActiveBurden compound gate and determine whether recovery/drawdown terms are necessary or redundant.

### C. Native H3 reconstruction

This is the highest-value investigation.

Test the recovered:

```text
ActiveBurden - early shock
```

behavior directly against the native `3_to_4` transition and distinguish it from generic hazard prediction.

### D. Native H4

Recover the missing aligned `4_to_4` panel. Until then, keep H4 at scout status.

### E. ExitBridge

Reproduce the next-trigger 6h/24h/48h AUCs using strict episode-end timing.

### F. PriorCarry

Verify pure one-episode shifting with first-null behavior and zero current-row contamination.

### G. Promotion

Run all six seats through the Promotion Court before allowing any runtime authority.

---

## 20. Immediate next experiment

Do **not** run another generic global tournament first.

Run the six-seat Promotion Court with transition-native features:

```text
0_to_4        -> FalseCalmIgnition
2_to_4        -> ResetDragRelease
3_to_4        -> RecoveryInversion
4_to_4        -> CeilingTrap/scout
ExitBridge    -> next-trigger timing
PriorCarry    -> continuation timing
```

For each seat measure:

```text
native target
native scope
A
B
A+B
A x B
A x B x C
AUC
Brier
calibration
LOYO stability
complexity
```

The selection question is:

> Which family combination is necessary and complementary **for this seat's actual transition**, not which combination happens to predict the whole dataset best?

---

## 21. Golden rules for future TIAMAT work

1. **Prediction is not permission.**
2. **Scope is part of the head's identity.**
3. **Timing lineage beats field names.**
4. **ExitBridge is current boundary state; PriorCarry is shifted previous boundary state.**
5. **ActiveBurden is current runtime burden and is not either of those.**
6. **Do not collapse all jobs into one scalar.**
7. **A x B is meaningful only inside the correct lane.**
8. **AUC without Brier/calibration is incomplete.**
9. **Out-of-sample stability beats an impressive in-sample interaction.**
10. **Final-label fields such as `episode_type` and `duration_bucket` are leakage risks in causal mechanism discovery.**
11. **Proxy findings remain proxies until native data reproduces them.**
12. **H4 is not native-confirmed until a proper 4_to_4 panel exists.**
13. **No head gets global authority merely because it wins a benchmark.**
14. **Promotion happens head-by-head through the court.**
15. **The goal is to reconstruct the controller, not manufacture the best predictor.**

---

## 22. Current status

**Recovered:**

- topology-native head scopes
- head names/roles
- ExitBridge/PriorCarry distinction
- short vs long continuation ownership
- important native gate thresholds
- H3 recovery-inversion anchor
- reason global scalar reduction failed
- reason heads must be scoped

**Partially recovered:**

- exact formulas for each head
- exact H0/H2/H3 calibration/weights
- ExitBridge full timing formula
- continuation thresholds

**Not yet natively confirmed:**

- 4_to_4 CeilingTrap
- final promotion of any head to runtime authority
- universal reduced mathematical core

**Most promising immediate target:**

> **Reconstruct and independently validate the six-seat Promotion Court using the native 43,848-row Layer-1 body and strict timing/scope rules.**

---

## 23. Provenance note

This handoff consolidates recovered TIAMAT work from the project/library materials, including the HF9 TIAMAT full-detail handoff, tiny-fact handoff, native Layer-1 data examination, TIAMAT experimental protocol, and later inference-core handoff.

Where older results conflict with newer native leakage-clean tests, the newer native result wins for scientific interpretation, while the older result is retained as historical evidence/hypothesis.

**Do not silently convert hypotheses into facts.**
