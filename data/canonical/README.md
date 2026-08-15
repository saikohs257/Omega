# Canonical Layer-1 artifact contract

The 2020–2024 source panel is an external canonical artifact, not a Git-tracked data file.

Required source:
`layer1_structured_hazard_arm_timeseries(15).csv`

Required SHA-256:
`6f0dc516fdf3313ab27a38d942504d073faccba4067877531b44c219c5e4b31a`

Required structural checks:
- 43,848 rows
- 15 source columns
- 169 native `3_to_4` starts (`entry_path == 3_to_4` and `episode_age_h == 1`)

CI/experiments must verify the SHA-256 and structural checks before using the artifact. The artifact is intentionally not committed to Git because it is a mixed evidence panel containing future labels and hindsight annotations. The canonicalizer creates separate causal, label, and annotation spines.

The canonicalizer is `experiments/canonicalize_layer1_causal_spine.py`.
