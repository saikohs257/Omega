# Future Experiment: Novel Structure Discovery

## Status

**Deferred experiment.** Do not mix this into the current evidence-gated tournament until the existing discovery and selection machinery is stable.

## Question

Can Omega/TIAMAT detect a genuinely useful structure when the true mechanism is not represented by the candidate vocabulary supplied to the system?

The goal is not merely to select the best existing hypothesis. The goal is to distinguish:

- a known mechanism that predicts well,
- a known mechanism that is misleading or redundant,
- disagreement between otherwise credible mechanisms,
- and observations that contain structure not adequately represented by the current hypothesis space.

## Proposed axes

Evaluate each candidate/world on at least:

1. **Prediction** — held-out discrimination and probabilistic skill.
2. **Calibration** — whether confidence matches observed frequency.
3. **Stability** — whether the result survives perturbation, resampling, and regime changes.
4. **Complexity** — explanatory structure achieved per added degree of freedom.
5. **Novelty** — distance from the existing candidate vocabulary and known families.
6. **Contradiction** — systematic evidence against the currently available explanations.
7. **Emergence** — whether a new relational structure repeatedly appears from otherwise weak components.
8. **Explanatory compression** — whether the proposed structure explains multiple observations with fewer assumptions.

## Experimental worlds

Build blinded synthetic worlds in which the generating mechanism is hidden from the selector:

- known single-variable mechanism;
- known interaction mechanism;
- delayed mechanism;
- regime-dependent mechanism;
- redundant mechanisms;
- no-signal world;
- mechanism deliberately absent from the supplied vocabulary;
- novel interaction that cannot be represented by the initial candidate grammar.

## Required behavior

If a known candidate wins with strong held-out evidence, return `SELECTED`.

If candidates disagree materially, return `CONTESTED` or `UNRESOLVED` rather than forcing consensus.

If no candidate explains the observations adequately, return `UNRESOLVED` with a machine-readable reason such as:

`NO_REPRESENTED_MECHANISM`

The system must **not invent a novel mechanism merely to avoid unresolved status**.

## Discovery extension

A later experiment may add a controlled hypothesis-generation stage:

```text
observations
    -> candidate grammar
    -> bounded combinations
    -> held-out evidence
    -> residual analysis
    -> novelty detection
    -> propose new relational hypotheses
    -> re-test on untouched holdout
```

Any proposed new hypothesis must be treated exactly like an ordinary candidate: blind evaluation, probability contract, calibration, Brier skill, stability, complexity, Pareto analysis, and an untouched confirmation holdout.

## Success criterion

The experiment succeeds only if Omega can:

1. correctly select represented mechanisms;
2. reject deceptive/high-AUC candidates;
3. recognize genuine disagreement;
4. remain unresolved when no represented mechanism is sufficient; and
5. later propose a novel structure that survives independent held-out confirmation without having been encoded in advance.

A failure to discover a novel mechanism is **not** itself a failure. False discovery would be the more serious failure.

## Guardrail

This experiment is exploratory research, not permission to weaken existing evidence gates. The current tournament remains the baseline comparator.
