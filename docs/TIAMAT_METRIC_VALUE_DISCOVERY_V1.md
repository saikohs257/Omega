# TIAMAT Metric Value Discovery v1

## Purpose

Omega must not assume that Brier, LogLoss, AUC, or any other metric is universally authoritative. The correct metric depends on the object TIAMAT is predicting.

## Target classes

- **EVENT** — binary transition/failure discrimination.
- **HIDDEN_STATE** — probability over latent structural states.
- **TIME_TO_TRANSITION** — time/horizon prediction.
- **TRAJECTORY** — direction and path evolution.
- **GUARD_OR_MODE** — discrete mode/guard prediction.

## Binary metric panel

For an event target, report at minimum:

- AUC — discrimination/ranking.
- Brier — probability accuracy.
- LogLoss — probability sharpness and correctness.
- Calibration error — reliability of stated probabilities.

AUC remains historically important because it was used in original TIAMAT evaluation. Brier is retained because it is appropriate for probabilistic predictions. Neither is promoted to universal authority by this module.

## Hidden-state panel

For a latent-state probability distribution, report:

- multiclass Brier,
- multiclass LogLoss,
- top-1 state accuracy.

This directly tests the possibility that TIAMAT's useful prediction object was belief about a hidden state rather than a binary transition.

## Scientific rule

Metric discovery is descriptive and must not optimize a metric against the same evidence used to validate the candidate models. Discovery and validation data must remain separated.

A metric can therefore be:

- useful for one target and weak for another;
- complementary rather than dominant;
- unresolved when evidence is insufficient.

No retrospective replacement of historical TIAMAT's original AUC evaluation is permitted.

## Next experiments

1. Run the binary panel on the existing tournament worlds.
2. Add hidden-state targets where the historical replay supports them.
3. Add transition-centered and lead-time metrics.
4. Compare instantaneous versus causal-memory candidates under every relevant metric.
5. Validate the discovered metric profile on fresh held-out evidence.
6. Only then decide whether tournament ordering should change.
