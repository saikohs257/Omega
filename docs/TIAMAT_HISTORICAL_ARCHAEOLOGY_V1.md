# TIAMAT Historical Archaeology V1

Research-only reconstruction from the May 2026 HF8/Hinge artifacts.

## Scope

This document records the recovered historical machinery without redefining the current Omega canonical runtime.

### Layered pipeline

1. Historical primitive substrate already present in the replay spine.
2. Active/admission state machine.
3. Entry lineage (`0_to_4`, `2_to_4`, `3_to_4`).
4. TheHinge run tracker (`trapped`, `mixed`, `phasic`, `run_age_h`).
5. Daily age chain and Hinge bifurcation-state feature.
6. Historical hazard construction / sidecar semantics.
7. V41E admission gate and V41F downstream rescue/owner machinery.
8. Runtime firewall / authority boundary.

## Recovered active/admission machine

Start edge:

```text
hazard_raw.diff() > 1.00
AND LiveDeficit > 0.85
AND SimpleShock > 0.50
```

Exit edge:

```text
hazard_score.diff() <= -0.17
AND SimpleShock.shift(6) > 0.33
```

Stateful update is edge-driven: exit has precedence while active; start only occurs while inactive.

This recovered machine was reported exact on the Layer1 historical substrate.

## Entry lineage

At active start, use the previous hour's `LiveDeficit`:

```text
<= 0.70       -> 0_to_4
0.70..0.85    -> 2_to_4
> 0.85        -> 3_to_4
```

Historical exception:

```text
if base == 3_to_4 and previous SimpleShock > 0.50:
    2_to_4
```

The resulting path is forward-filled only while the episode is active.

## TheHinge

The recovered tracker classifies episode type at entry:

- `3_to_4`: `trapped`, `phasic`, or `mixed`.
- `2_to_4`: `trapped` or `mixed`.
- `0_to_4`: `trapped` or `mixed`.

Gate precedence is critical:

1. trapped check at `hazard_score >= 0.966`;
2. phasic scoring using shock, volume tempo, prior hazard peak, and episode tempo;
3. default to mixed.

Phasic has an 8-hour maximum duration. A still-active phasic run reclassifies to trapped after that boundary.

## Age chain

From hourly `run_age_h`:

```text
qualified active hours
  -> daily maximum age
  -> 7-day rolling mean
  -> 180-day rolling z-score
```

## Hinge

Recovered frozen historical Hinge v3a:

```text
coil_tension_raw =
    0.4 * z_vol_comp_180
  + 0.4 * z_volm_comp_180
  + 0.2 * z_range_comp_180

hinge_v3a =
    0.70 * z_coil_tension_180
  + 0.30 * z_age_stall_7_180
```

Historical interpretation: a composite bifurcation/inflection-state marker, not a directional signal by itself.

## V41E

The recovered May-23 packet explicitly supersedes earlier quarantine language and promotes `v41e_gate_v1` as the canonical historical admission gate for the recovered Layer1/V41F substrate.

Inputs are causal/prior only:

- `hazard_raw_0_4h_max_from_l1`
- `SimpleShock_0_4h_max_from_l1`
- `prev_active_exit_SimpleShock`

The gate admits rows into `short_watch`; it does not own long/short action, and V41F remains downstream.

## Authority boundary

The historical firewall treats hazard and related sidecars as scoped evidence. They are not universal owner routers and must not silently override owner/rescue logic.

## Missing-source boundary

The native original generator for hourly `LiveDeficit` remains unrecovered. This reconstruction therefore consumes historical `LiveDeficit` values when present rather than inventing a replacement generator.

## Relationship to current Omega

This module is historical/research-only. It does not redefine `tiamat.state.TiamatState`, the current deterministic engine, or the current canonical runtime contract.
