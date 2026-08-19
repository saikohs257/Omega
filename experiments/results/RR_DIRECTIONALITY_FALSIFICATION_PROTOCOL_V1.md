# RR Directionality Falsification Protocol V1

Status: experimental / non-promotable until resolved.

Question: does `rr_recovery_minus_burden` fail because it contains no information, or because the falsification scoring convention is directionally inverted / estimator-dependent?

The experiment evaluates both `+feature` and `-feature` under:

1. the same logistic estimator used by `hydra_relative_recovery_court_v1.py`;
2. the rank-based scorer used by the existing anti-leakage court.

Evaluation uses the same 2024 frozen holdout and 72 non-overlapping phase offsets. The canonical spine is not modified and the derived feature is reconstructed through the existing `history()` transform.

Interpretation:

- logistic and rank both near 0.50 in both orientations: no robust information;
- one orientation near 0.50 and the reverse near 0.50: no robust information;
- reverse orientation materially above 0.50: sign inversion is implicated;
- logistic strong while rank weak: estimator/scoring mismatch is implicated;
- both estimators strong only in limited offsets: phase/regime dependence remains unresolved.

No result from this experiment is automatically promotable into canonical runtime or Senate authority.
