# TIAMAT 20-World Tournament V1

This suite is a synthetic discovery harness for the adaptive model-selection layer. It is not evidence about the historical TIAMAT corpus.

## Worlds

1. damage
2. recovery
3. charge
4. momentum
5. residual momentum
6. residual load
7. forcing
8. flow
9. initial velocity
10. initial momentum
11. initial trajectory
12. path
13. trajectory
14. arc
15. route
16. track
17. orbit
18. resistance
19. coupling
20. interaction-only combination

## Expected behavior

- In worlds 1–19, the informative singleton should beat neutral and misleading candidates.
- In world 20, the signal exists only in the `charge + coupling` interaction; the tournament should select that combination.
- A separate insufficient-evidence case must remain `UNRESOLVED`.

## Evidence rules

Each world uses held-out predictions. Selection considers AUC, Brier score, log loss, calibration error, stability, and complexity. The tournament does not promote a result into canonical TIAMAT state.

The purpose is to test the selector's reasoning machinery before introducing real corpus evidence. A synthetic winner is a test pass, not a scientific claim.
