# TIAMAT Claim Ledger V1

Status: reconciliation control artifact. This ledger separates recovered evidence from canonical runtime behavior.

| Claim / concept | Classification | Current evidence | Runtime status | Rule |
|---|---|---|---|---|
| Seven legal modes Q/P/E/C/H/R/Rf | CONFIRMED | `tiamat/modes.py`, `tiamat/transition.py` | CANONICAL | May be used by runtime |
| M3 state `[B,V,D]` | CONFIRMED | `tiamat/state.py`, reconciliation document | CANONICAL CANDIDATE | Primary reduced state; do not silently expand |
| `tau_D`, `tau_mode` | CONFIRMED | `tiamat/state.py` | CANONICAL TEMPORAL STATE | Memory variables, not fixed timers |
| recovery = `max(0,-V)` | CONFIRMED | `tiamat/state.py` | CANONICAL DERIVED OBSERVABLE | Derived from current state |
| pressure = `max(0,V)` | CONFIRMED | `tiamat/state.py` | CANONICAL DERIVED OBSERVABLE | Derived from current state |
| momentum = `V` | CONFIRMED | `tiamat/state.py` | CANONICAL DERIVED OBSERVABLE | Derived from current state |
| residual load = `max(0,D-recovery)` | CONFIRMED | `tiamat/state.py` | CANONICAL DERIVED OBSERVABLE | Derived from current state |
| Guard vocabulary / precedence | CONFIRMED | `tiamat/guards.py`, `tiamat/transition.py` | CANONICAL RUNTIME | Preserve explicit precedence |
| Shared live/replay transition law | CONFIRMED | `tiamat/transition.py`, `tiamat/replay.py` | CANONICAL RUNTIME | No divergent replay implementation |
| Legal transition table | CONFIRMED | `tiamat/transition.py` | CANONICAL RUNTIME | Illegal transitions must fail |
| M0-M7 identification registry | CONFIRMED | `tiamat/identification_registry.py` | IDENTIFICATION ONLY | Never treat registry as second runtime |
| M7 permanent control | CONFIRMED | identification registry | CONTROL ARM | Preserve as control |
| SimpleShock | DERIVED / HISTORICAL | recovered research corpus | NOT CANONICAL YET | Requires source-linked derivation |
| LiveDeficit | DERIVED / HISTORICAL | recovered research corpus | NOT CANONICAL YET | Requires source-linked derivation |
| RecoveryWeakness_v1 | DERIVED / HISTORICAL | recovered research corpus | NOT CANONICAL YET | Requires source-linked derivation |
| hazard_raw / hazard_score | HISTORICAL / UNRESOLVED | recovered research corpus | NOT CANONICAL YET | Do not duplicate hazard law |
| hinge | DERIVED / HISTORICAL | recovered research corpus | NOT CANONICAL YET | Diagnostic until independently reconciled |
| damage update equation | UNRESOLVED | historical notes mention it | MISSING | Do not invent coefficients |
| recovery update equation | UNRESOLVED | historical notes mention it | MISSING | Do not invent coefficients |
| residual-load update equation | UNRESOLVED | historical notes mention it | MISSING | Do not invent coefficients |
| momentum update equation | UNRESOLVED | historical notes mention it | MISSING | Do not invent coefficients |
| refractory thresholds | PARTIAL / UNRESOLVED | transition surface has inputs | PARTIAL | Need evidence-backed threshold table |
| promotion thresholds | PARTIAL / UNRESOLVED | guard/transition surface | PARTIAL | Need evidence-backed threshold table |
| hysteresis rules | UNRESOLVED | research describes hysteresis | MISSING | Need source evidence before promotion |
| historical probability output | INCOMPARABLE | historical outputs are diagnostic | FIREWALLED | Never silently promote to probability |

## Required reconciliation rule

A historical concept may enter canonical runtime only when its provenance is tied to source evidence and a deterministic implementation/test exists. Otherwise it remains historical, derived, inferred, hypothesized, falsified, or unresolved.

## Minimum next evidence package

1. Source artifact for each claimed update equation.
2. Exact coefficient/threshold provenance where available.
3. Counterexamples or tests supporting guard precedence.
4. Replay fixtures showing deterministic state trajectories.
5. Explicit probability projection only if a validated probability contract is established.
