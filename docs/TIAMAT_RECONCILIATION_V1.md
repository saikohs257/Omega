# TIAMAT Reconciliation V1

> Status: evidence-backed reconciliation map. This document aligns the recovered TIAMAT research state with the current `tiamat/` implementation on `main`.

## 1. Ground truth from the repository

The repository README states that TIAMAT is the seventh canonical build-order layer and describes its runtime surface as explicit and deterministic: seven-mode state machine, M3 primary reduced state `[B, V, D]`, optional temporal state `tau_D` / `tau_mode`, derived observables (recovery, pressure, momentum, residual load), explicit guard evaluation, legal transition table, shared live/replay transition function, canonical telemetry projection, M0–M7 identification registry, and deterministic temporal holdout evaluation. It also states that the identification layer is an evaluation surface, not a second runtime. fileciteturn12file0

That means TIAMAT in `main` is not a single script and not merely a benchmark wrapper. It is a layered subsystem.

## 2. What is already explicit in code

### A. State

`tiamat/state.py` defines the runtime state object with fields `B`, `V`, `D`, `tau_D`, `tau_mode`, `mode`, and `model_id`. It derives `recovery`, `pressure`, `momentum`, and `residual_load` directly from those fields. fileciteturn1file0

### B. Modes

`tiamat/modes.py` defines the seven legal modes: `Q`, `P`, `E`, `C`, `H`, `R`, and `Rf`. fileciteturn5file0

### C. Guards

`tiamat/guards.py` implements named guard families and priorities, including the recovered guard vocabulary used in the research notes: `DURATION_DAMAGE_HAZARD_GUARD`, `RELAXATION_WITH_RESIDUAL_DAMAGE`, `EXCITATION_DURATION_EXPIRED`, `LATENT_HAZARD_PRECURSOR_GUARD`, and `COUPLED_TRANSFER_HAZARD_PROMOTION`. fileciteturn4file0

### D. Transition law

`tiamat/transition.py` uses guard-triggered precedence and legal transition tables to update the state, including the relaxation-with-residual-damage relapse path. fileciteturn3file0

### E. Replay

`tiamat/replay.py` replays evidence through the same transition function. That is important because live and replay semantics are shared rather than forked. fileciteturn8file0

### F. Projection

`tiamat/projection.py` currently projects the state by returning `state.to_dict()`. This is consistent with the subsystem being a state machine first and a predictive interface second. fileciteturn11file0

### G. Registry and identification surface

`tiamat/identification_registry.py` keeps M0–M7 registered, with M3 as the primary reduced-state candidate and M7 as the permanent control arm. It also preserves candidate thresholds and the retired fixed six-hour choke timer. fileciteturn7file0

## 3. What the recovered research says TIAMAT is doing

The consolidated evidence supports TIAMAT as a structural-dynamics reconstruction system, not just a scalar classifier.

The recovered semantics separate at least four kinds of content:

1. **Observed inputs**: telemetry, replay evidence, source snapshots.
2. **Derived observables**: recovery, pressure, momentum, residual load.
3. **Latent state**: the hidden mechanism the replay is trying to recover.
4. **Controller behavior**: guards, durations, hysteresis, refractory logic, and legal transitions.

That is why the research repeatedly emphasizes damage, recovery, residual load, momentum, mode age, promotion thresholds, and guard precedence.

## 4. What is fully aligned

These parts of the current implementation are aligned with the recovered TIAMAT picture:

- The seven-mode topology.
- The M3 reduced-state candidate framing.
- Derived observables from the current state representation.
- Guard names and precedence.
- A single canonical transition function used by both live and replay surfaces.
- Identification registry plus permanent control arm.
- Deterministic holdout / validation split machinery.
- The principle that the identification layer is not a second runtime.

## 5. What is only partially aligned

### A. Rich latent dynamics

The research record suggests a richer latent structure than the current explicit runtime state. The code has the minimum public state object, but the recovered research also talks about damage/recovery laws, residual load dynamics, momentum evolution, refractory thresholds, promotion thresholds, and hysteresis rules as deeper semantic layers.

That does not mean the code is wrong. It means the current runtime surface is a compact representation of a larger recovered hypothesis space.

### B. Historical probability semantics

The probability-interface issue is real: historical TIAMAT did not present itself as a modern calibrated probability predictor. So a runner that requires explicit probability contracts should record historical TIAMAT as `INCOMPARABLE` rather than silently translating its outputs into probabilities.

This is not a rejection of TIAMAT. It is an interface boundary.

### C. Runtime-engine breadth

The repo still contains a generic `TiamatEngine.evaluate()` surface that acts as an allow/reject request gate. That is useful, but it is not the full structural controller described in the research record. The engine is therefore only a partial embodiment of the recovered TIAMAT model.

## 6. What is missing or not yet reconciled

These items are not fully recovered into the current implementation and should be treated as open reconciliation work:

- explicit canonical equations for damage, recovery, and residual-load update laws;
- a formally declared minimum latent state vector with epistemic labels on each component;
- complete guard-firing semantics for all recovered guard families;
- explicit hysteresis / refractory / promotion threshold rules where supported by evidence;
- a formal historical-vs-native probability interface boundary in the runtime API;
- a line-by-line provenance map showing which reconstructed claims are observed, derived, inferred, or still hypothetical.

## 7. What should not happen

Do not collapse TIAMAT into one scalar score.
Do not retrofit historical TIAMAT into a probability contract just to make benchmarking easier.
Do not treat the identification surface as if it were the runtime itself.
Do not erase the distinction between recovered evidence and canonicalized runtime behavior.

## 8. Recommended reconciliation order

1. Freeze the evidence labels for each recovered TIAMAT claim.
2. Map each claim to the exact current file or test that supports it.
3. Mark each item as `OBSERVED`, `DERIVED`, `INFERRED`, `HYPOTHESIZED`, `CONFIRMED`, `FALSIFIED`, or `UNRESOLVED`.
4. Add only the missing pieces that are strongly supported by evidence.
5. Keep historical TIAMAT `INCOMPARABLE` unless and until a validated probability projection is explicitly established.
6. Re-run the identification, replay, and holdout surfaces after reconciliation.

## 9. Bottom line

TIAMAT in `main` is already a serious structural-state subsystem, not a toy predictor. The recovered research says the subsystem is about hidden state, transitions, guards, and trajectory dependence. The current code matches that core shape, but the full research picture is still larger than the present runtime surface.

The next artifact should be a provenance-aware claim ledger that ties each recovered TIAMAT statement to either source evidence, current code, or a clearly marked hypothesis.
