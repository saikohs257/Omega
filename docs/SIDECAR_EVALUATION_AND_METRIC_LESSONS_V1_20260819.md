# Sidecar Evaluation & Metric Lessons V1 — 2026-08-19

## Purpose
Freeze the lessons learned during the August 19 metric/orientation/sidecar audit so they are not lost between sessions.

## 1. Core lesson: do not force every mechanism through AUC
AUC measures ranking/separation. It is not a universal utility measure. A sidecar can be useful for routing, calibration, trust, novelty, disagreement, or local attention without being a strong global predictor.

## 2. Sidecars need four evaluation axes
Every sidecar should be evaluated for:

1. VALUE — does it separate, improve a decision, or add useful information?
2. CALIBRATION — are its probabilities credible?
3. FAILURE — where does it break by regime/path/phase/load?
4. COST — how much structural complexity, data dependency, runtime, and governance burden does it introduce?

## 3. Metric orientation is part of the contract
AUC: higher is better.
Brier: lower is better.
Log loss: lower is better.
There is no universal `1 - metric` transformation for Brier or log loss.

## 4. AUC inversion lesson
A genuine polarity inversion can produce AUC near 0 when the reversed score has AUC near 1. The `rr_recovery_minus_burden` investigation demonstrated this directly under a rank-score orientation mismatch: approximately 0.0496 versus approximately 0.9504 after reversing the score.

This is a confirmed scoring/orientation issue for that specific rank-court result, not evidence that all low AUCs are inverted.

## 5. Archaeology-parser lesson
The preliminary historical AUC inversion scanner initially reported 12 near-perfect inversions. That result was later invalidated because the parser treated generic numeric Markdown table cells as AUC. Values such as `0.045041` were log-loss values, not AUC values.

After the parser was corrected to use explicit AUC/ROC-AUC labels and AUC table columns, the corrected screen found:

- 2 explicit AUC values below 0.50;
- 0 values in the 0.040–0.053 band;
- 0 near-perfect inversion candidates.

The two low AUC observations were `entry_ret24h = 0.4633` and `entry_live_pressure_delta_abs = 0.4845`; their reflected values were only 0.5367 and 0.5155.

Therefore the earlier `80% inversion` claim is withdrawn as a parser artifact.

## 6. What remains confirmed
The independent RR directionality experiment remains valid: its logistic result was approximately 0.9504 while the rank score in the tested orientation produced approximately 0.0496, and reversing the rank score restored approximately 0.9504. That is the concrete demonstrated inversion case.

## 7. Probability metrics lesson
A separate probability-metric orientation audit established:

- Brier is lower-is-better;
- log loss is lower-is-better;
- synthetic complemented probabilities substantially worsen both metrics.

The repository archaeology found one Brier-threshold mention and no explicit historical log-loss metric rows in the scanned text corpus. This is insufficient to establish any historical Brier/log-loss inversion problem.

## 8. Complexity lesson
Complexity must be treated as an evaluation axis. A sidecar does not automatically justify its structural cost because it has a slightly higher AUC.

Complexity should include, where applicable:
- number of inputs;
- transformations;
- interaction depth;
- conditional branches;
- learned parameters;
- temporal/history dependence;
- dependencies on other sidecars;
- runtime cost;
- interpretability burden;
- governance/authority burden.

## 9. Complexity must earn its keep
A useful sidecar should be compared on a Pareto frontier rather than by a single score. A simpler mechanism with slightly lower discrimination may dominate a much more complex mechanism when calibration, stability, or governance burden are considered.

## 10. Sidecar failure surfaces
Global metrics can hide local failure. Sidecars should be evaluated by:
- regime;
- path;
- phase/age;
- burden/load state;
- activation state;
- other architecture-relevant strata.

Record both average and worst-case behavior.

## 11. Worst-case metrics are diagnostic, not promotional
High Brier or high log loss can be useful for locating failure surfaces even though lower values are better for ordinary prediction quality.

Therefore sidecar analysis should report:
- mean/global quality;
- worst-regime quality;
- worst-path quality;
- worst-phase quality;
- worst relevant interaction cell.

## 12. Governance lesson
No sidecar should be promoted because one metric looks good. A sidecar should carry explicit evidence references, calibration status, failure surface, complexity, and authority status.

## 13. Negative knowledge is evidence
A failed sidecar is not automatically deleted. Preserve:
- what was tested;
- what metric was used;
- what protocol was used;
- why it failed;
- whether the failure was representation-specific, estimator-specific, scoring-specific, or conceptual.

## 14. Provenance before promotion
Repeated numbers in multiple reports are not independent discoveries until their computational provenance is established. Repeated manifestations of one implementation defect must not be counted as separate variables.

## 15. Audit ladder
The preferred audit order is:

1. verify the result artifact;
2. verify metric labeling;
3. verify polarity/orientation contract;
4. verify estimator/scoring method;
5. verify temporal protocol;
6. verify target construction;
7. verify provenance and independence;
8. only then interpret the variable or mechanism.

## 16. Current architecture implication
The system should distinguish at least:
- predictive signals;
- routing/annotation sidecars;
- trust/calibration mechanisms;
- disagreement/audit mechanisms;
- governance seats.

A sidecar can be useful without becoming a predictor or Senate authority.

## 17. Working sidecar doctrine
> Every sidecar gets tested for VALUE, CALIBRATION, FAILURE, and COST.

No promotion based on one metric.
Complexity must earn its keep.

## 18. Open work
The next high-value audit is to identify the actual computations producing historical Brier/log-loss values and evaluate their probability orientation and calibration directly, instead of relying on report-table archaeology alone.

A second high-value audit is to review known AUC-producing courts for explicit sign controls, with `rr_recovery_minus_burden` as the confirmed case study.

## Evidence refs
- Corrected AUC screen run: `32308529173`
- Probability metric orientation audit run: `32309644705`
- RR directionality result: `32303960481`
- Original Hydra conditional ablation implementation: `experiments/hydra_conditional_ablation_v1.py`
- Hydra calibration implementation: `experiments/hydra_calibration_court_v1.py`
