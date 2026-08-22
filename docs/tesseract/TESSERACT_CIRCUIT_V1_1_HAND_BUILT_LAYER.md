# TESSERACT_CIRCUIT V1.1 — Hand-Built Layer

**Status:** RECOVERED / REFERENCE IMPLEMENTATION / DIAGNOSTIC-ONLY

## Exact source

Primary source artifact:

`TESSERACT_CIRCUIT_V1_1_COMPONENT_FREEZE_20260628.tar.zst`

Authoritative frozen tables:

- `tables/EDGE_VOLTAGE_DEFINITIONS.csv`
- `tables/EDGE_OHMS_CONDUCTANCE_DEFINITIONS.csv`
- `tables/BASIN_CAPACITANCE_DEFINITIONS.csv`
- `tables/CONTINUITY_INDUCTANCE_DEFINITIONS.csv`
- `tables/LEGAL_ADJACENCY_STRICT_SPEC.csv`
- `tables/RELEASE_SWITCH_STATE_MACHINE.csv`
- `tables/LEAKAGE_ROLE_REGISTER.csv`
- `tables/AUTHORITY_GATE_DEFINITIONS.csv`
- `tables/EDGE_COMPONENT_SOURCE_MAP.csv`

Reference source:

`src/component_freeze_v1_1_reference.py`

## Canonical hand-built components

The V1.1 hand-built layer defines deterministic, source-backed component semantics before any learned edge weighting:

1. edge-local residual voltage;
2. empirical smoothed edge conductance;
3. effective ohms as inverse conductance;
4. basin capacitance as empirical hold-continuation/storage probability;
5. continuity as an empirical path prior with reversal escape;
6. explicit release-state permission;
7. strict legal-edge admission;
8. leakage-role enforcement;
9. component-level authority, shuffle, split, ablation, and failure gates.

## Critical boundary

This layer is **not** runtime authority and is **not** a learned model.

Learned weights remain downstream of the strict table, replay, ablation, shuffle, split, known-error court, and authority gates.

## Frozen ohms rule

For an eligible train risk set:

`conductance = (edge_release_count + alpha) / (risk_set_count + alpha + beta)`

with the frozen conservative prior `alpha=1`, `beta=9` unless an evidence-backed edge-specific prior is justified.

`effective_ohms = min(ohms_cap, 1 / (epsilon + conductance))`

## Leakage rule

Future/released labels such as `realized_edge`, `did_edge_happen`, `actual_next_edge`, and release-timing targets are target/audit roles and are blocked from live features.

## Next gate

Build `TESSERACT_CIRCUIT_TABLE_V1_1_STRICT` using these definitions. Do not promote learned weights until the hand-built table and its replay/provenance courts pass.
