# TIAMAT-Lite-1 Ablation Results — 2026-08-14

Frozen 2024 holdout; no threshold retuning.

| Model | Match | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full Lite-1: Δhazard + LD + shock | 100.0000% | 1.0000 | 1.0000 | 1.0000 | 773 | 0 | 0 |
| Remove LD: Δhazard + shock | 99.9772% | 0.9974 | 1.0000 | 0.9987 | 773 | 2 | 0 |
| Remove shock: Δhazard + LD | 100.0000% | 1.0000 | 1.0000 | 1.0000 | 773 | 0 | 0 |
| Δhazard only | 99.9772% | 0.9974 | 1.0000 | 0.9987 | 773 | 2 | 0 |

## Result

`SimpleShock` is redundant for the frozen Lite-1 admission behavior on the 2024 holdout. Removing it produced zero changed active rows. Therefore Lite-1 can be simplified to:

```text
Δhazard_raw > 1.00
AND LiveDeficit > 0.85
```

with the recovered exit edge:

```text
Δhazard_score <= -0.17
AND SimpleShock[t-6] > 0.33
```

Important: this result does NOT prove SimpleShock is globally redundant in TIAMAT. It is redundant only for this frozen Lite-1 admission test on the 2024 holdout. The exit edge still contains SimpleShock and therefore it remains part of the current Lite implementation.

Removing LiveDeficit caused only 2 false positives, so LD is still justified as a structural admission filter in the frozen test.
