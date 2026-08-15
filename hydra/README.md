# HYDRA — Streamlined, Compartmentalized TIAMAT Successor

HYDRA is a new architecture built from the forensic TIAMAT work. It is **not** a claim that the historical TIAMAT source has been replaced or exactly reconstructed.

## Design goal

Do not make the entire system small by deleting useful mechanisms. Make it **streamlined and enhanced** by giving each mechanism one job and allowing each compartment to evolve independently.

```text
                     SHARED STATE BUS
                            |
       +--------------------+--------------------+
       |         |          |          |         |
     Hazard    Burden    Recovery   Trajectory Persistence
       |         |          |          |         |
       +--------------------+--------------------+
                            |
                    Lane Coordinator
                 +----------+----------+
                 |          |          |
                H0         H2         H3
```

## Compartments

### Hazard
Measures structural pressure/elevation. The starting implementation consumes the recovered `hazard_score` directly.

### Burden
Tracks current unresolved load via `LiveDeficit`.

### Recovery
Exposes recovery capacity as `1 - RecoveryWeakness_v1`.

### Trajectory
Tracks transition direction. HYDRA v0 uses a deliberately small hazard-acceleration baseline so the interface can later be upgraded without changing the state bus.

### Persistence
Tracks age independently. It is not allowed to smuggle final episode labels or future information into the live state.

### Lane coordinator
Routes the observation into the recovered topology scopes using the previous-hour LiveDeficit partition and applies lane-specific projections. These projections are starting mechanisms, not canonical TIAMAT coefficients.

## Important safeguards

1. `tiamat/` remains untouched and serves as the historical/reference implementation.
2. HYDRA modules expose independent state estimates; the coordinator preserves disagreement telemetry.
3. Final labels such as `episode_type` and `duration_bucket` are never accepted as predictors by the core engine.
4. Lane-specific meaning is preserved; H0/H2/H3 are not forced into one universal scalar.
5. Every module can be replaced or enhanced independently and tested by differential comparison against TIAMAT or native panels.

## Current status

This is **HYDRA v0 architecture**, not a promoted production model. Its first job is to provide a clean experimental substrate for module-by-module enhancement and conformance testing.

## Next development targets

- exact raw-input adapters for canonical 43,848-row replay;
- module-level differential harness against TIAMAT;
- calibration and uncertainty per module;
- better trajectory state using causal temporal windows;
- persistence hysteresis and release modeling;
- coordinator policy learned from native lane outcomes without label leakage;
- ablation tests proving which module complexity earns its place.
