# Hydra Conditional Ablation — Execution Blocker

The conditional ablation court is implemented and CI-wired, but the full scientific run is currently blocked by the canonical-data contract.

## Evidence

The repository contract states that `layer1_structured_hazard_arm_timeseries(15).csv` is an **external canonical artifact**, intentionally not Git-tracked. Required SHA-256:

`6f0dc516fdf3313ab27a38d942504d073faccba4067877531b44c219c5e4b31a`

Required structure: 43,848 rows and 169 native `3_to_4` starts.

The current CI correctly fails when that source is absent rather than reconstructing or bypassing the gate.

## Current CI evidence

Run #680 (`31905704970`) checked out commit `fe15a77babc51e69c65d4594c68869cc5f765b5f` and successfully completed the full TIAMAT preflight. The canonical-data gate then failed because:

`data/canonical/layer1_structured_hazard_arm_timeseries.csv` does not exist in the repository workspace.

All Hydra court steps were consequently skipped.

## Decision

Do **not** commit a reconstructed CSV and do **not** weaken the SHA/row-count/H3 gate. The source must be supplied through an explicit external artifact mechanism, or the experiment must be run in an environment where the canonical file is mounted.

## Next valid execution paths

1. Mount/supply the exact canonical 15-column source with the required SHA-256 before the CI court step.
2. Alternatively, publish the exact source as an authenticated workflow artifact or other controlled external input and have CI fetch and verify it.

Until that happens, no conditional head promotion/merge/rejection claim is valid.
