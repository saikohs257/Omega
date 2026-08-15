# HYDRA Head Emergence Court V1 — Forensic Audit

Date: 2026-08-15

## Verdict

**Instrument: CONDITIONAL PASS**

**Scientific conclusions: NOT YET ADMISSIBLE for architecture promotion.**

The repository CI proves the codebase and current test suite are healthy, but the normal `test.yml` workflow only builds/installs Omega and runs `pytest`; it does not execute the Head Emergence Court itself. Therefore a green CI result is not evidence that the full scientific court ran in CI.

## Critical findings

### C1 — Head-job target mismatch

The implementation uses `Crash72` as the universal target, including for the Hazard head, while the stated head job is ranking/separation of impending structural hazard. This makes the Hazard result a Crash72 classifier, not a direct Hazard-state detector. A result described as "Hazard" must not be interpreted as evidence about episode-state detection unless that target is explicitly supplied.

**Severity: CRITICAL**

### C2 — Conditional features derive from native hidden-state labels

`make_history()` constructs `episode_starts24/48/72` from `entry_path == 3_to_4` and `episode_age_h == 1`. The same implementation declares `entry_path` a forbidden predictor, yet derived columns built from it can enter the persistence pool. `episode_age_h` is also directly used to create `age__log` and `age__saturation`.

This violates the intended boundary that Hydra should discover state from observable inputs rather than import reconstructed TIAMAT state through feature engineering.

**Severity: CRITICAL**

### C3 — Brier/calibration objective uses class-balanced logistic probabilities

The estimator uses `class_weight="balanced"` and the resulting `predict_proba` values are then scored with Brier, log loss, and calibration MAE. Class weighting changes the effective class prior seen during fitting; the resulting probabilities are therefore not automatically calibrated to the real event prevalence. Brier and calibration numbers can be materially distorted unless a separate calibration stage is fitted inside each training fold.

Scikit-learn explicitly distinguishes proper probabilistic scoring from calibration and warns that Brier alone is not a pure calibration measure. urlCalibration documentationhttps://scikit-learn.org/stable/modules/calibration.html

**Severity: CRITICAL**

### C4 — Selection score and discovery estimate are reused

The feature-search algorithm repeatedly scores candidate subsets on discovery folds, selects the winner from those same scores, and then reports those discovery scores. That is a model-selection estimate, not an unbiased estimate of generalization. A nested outer loop is required if the discovery score is to be presented as an honest performance estimate. Scikit-learn explicitly documents the optimism caused by non-nested selection and recommends nested CV when model selection is part of the procedure. urlNested versus non-nested cross-validationhttps://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html

**Severity: HIGH**

### C5 — `lo_year_scores()` is leave-one-year-out, not walk-forward

For a 2021 test year, the training set contains 2022 and 2023. That is temporally retrospective. It may be useful as a stability experiment, but it must not be labeled walk-forward or causal forecasting.

**Severity: HIGH**

### C6 — The 2024 holdout is used only once, but becomes the de facto arbiter for repeated research iterations

As currently structured, repeated experiments can inspect 2024 and then alter the court. Even without code leakage, repeated researcher interaction with a single holdout turns it into a tuning set. A proper research program needs an outer untouched test period or rolling nested evaluation for promotion decisions.

**Severity: HIGH**

### C7 — Candidate pools are manually constrained by feature names

The court is described as allowing states to emerge, but `pool_for_head()` assigns candidates to heads using string rules such as `"hazard" in name`, `"livedeficit" in name`, `"recovery" in name`, and `"age"`/`"episode_starts"`. This means the experiment is not fully blind to the current conceptual architecture.

This does not invalidate the experiment, but it means it is **constrained head discovery**, not unconstrained state discovery.

**Severity: HIGH**

### C8 — Floating search itself is reasonable, but its criterion is hand-designed

Floating search legitimately permits dynamic addition/removal and is an established feature-selection family. urlPudil et al. floating searchhttps://doi.org/10.1016/0167-8655(94)90127-9

However, the court's head objectives and coefficient weights are hand-written. Those weights therefore define part of what "emerges." The weights need to be frozen before a new scientific run and treated as methodology, not tuned from results.

**Severity: MEDIUM**

## What survives the audit

- Causal lag/rolling construction is directionally correct for the basic numeric signals.
- A separate untouched holdout is conceptually correct.
- Permutation controls are useful as a null test.
- Complexity penalties and floating add/remove search are defensible as search machinery.
- Reporting AUC, PR-AUC, Brier, log loss, and calibration error together is stronger than relying on one metric.
- The current design explicitly preserves the ability to reject or merge heads rather than assuming five heads must survive.

## Required V2 corrections before scientific promotion

1. Define a head-specific target for each head. Do not use Crash72 universally.
2. Remove all native TIAMAT hidden-state fields and all derivatives of those fields from the discovery pool unless the experiment explicitly defines them as allowed observations.
3. Replace class-balanced probability fitting with prevalence-correct probability estimation plus fold-local calibration, or use a model whose training objective preserves the event prior.
4. Make feature selection nested inside an outer temporal evaluation loop.
5. Replace leave-one-year-out stability with strict forward training: train on years < Y, test on Y.
6. Reserve a genuinely untouched final test period that cannot be inspected during development.
7. Freeze head objectives and their weights before the next run.
8. Add an explicit conditional-ablation stage: Hazard → +Burden → +Recovery → +Persistence → +Trajectory, with incremental AUC/PR-AUC and probability metrics.
9. Add a feature provenance manifest that proves every candidate is observable at prediction time.
10. Add a dedicated workflow step that actually executes the court and stores the result artifact; repository-green must not be confused with scientific-green.

## Audit disposition

The current head-emergence results should be retained as **exploratory evidence**, not discarded. Their most useful finding is the apparent convergence of Burden/Recovery/Persistence candidates. But that convergence is not yet sufficient to claim architectural redundancy because the target, feature provenance, calibration, and selection protocol are not yet clean enough.

**No Hydra head should be promoted, merged, or deleted from this V1 result.**
