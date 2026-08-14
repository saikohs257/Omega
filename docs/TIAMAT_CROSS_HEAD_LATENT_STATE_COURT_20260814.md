# TIAMAT Cross-Head Latent-State Court

Date: 2026-08-14

## Result

A single small latent state vector does not dominate all three native transition heads under leave-one-year-out validation.

### Native entry-head sample
- 0_to_4: 63 starts
- 2_to_4: 221 starts
- 3_to_4: 169 starts

## Candidate state results (mean LOYO AUC)

| Head | Best compact state | Mean AUC |
|---|---|---:|
| H0 / 0_to_4 | hazard + recovery | 1.000 |
| H2 / 2_to_4 | hazard + burden | 0.893 |
| H3 / 3_to_4 | full state/history candidate | 0.804 |

The full common state did not improve H0/H2 and did not solve H3.

## Held-out H3 check

A full causal feature set trained on 2020-2023 and tested on 2024 produced H3 AUC = 0.6696. This is not sufficient to claim a recovered H3 classifier.

## Interpretation

The evidence supports topology-native projections rather than one universal predictor. The most economical current interpretation is:

- H0: hazard/recovery context, shock-led ignition semantics.
- H2: hazard + burden, with recovery as context rather than a universal additive component.
- H3: hazard history + tempo/volume/shock context; the exact canonical phasic/mixed logic is still unresolved.

## Forensic classification

### Canonical / strongly supported
- Heads are topology-scoped.
- The native hourly panel contains 63 H0, 221 H2, 169 H3 starts.
- The recovered controller has a hard H3 trapped boundary at hazard_score >= 0.966.

### Reconstruction
- H0 hazard+recovery compact state.
- H2 hazard+burden compact state.
- H3 tempo/history interpretation.

### Unresolved
- Exact H3 native classifier outside the hard trapped branch.
- Whether the same upstream latent variables are shared across heads before projection.

## Next attack

Do not add more generic predictors. Recover the exact H3 branch implementation and its intermediate inputs, then compare every intermediate value against the native replay before attempting another fit.
