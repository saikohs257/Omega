# HYDRA Head Conditional Ablation Court V1 — 2026-08-15

## Data

Canonical uploaded Layer-1 spine: 43,848 hourly rows, 2020-2024.
Crash72 prevalence by year: 2020=207, 2021=443, 2022=251, 2023=0, 2024=67.

The 2023 target is single-class (zero Crash72 positives), so ROC/PR AUC for that year is undefined and is not interpreted as evidence for or against a head. Its probability metrics remain reportable.

## Calibration method

Nested logistic regression with 3-fold sigmoid probability calibration was fit only on pre-2024 data for the primary 2024 holdout results. Native episode labels and future outcome fields were not used as predictors.

## Candidate head representations

- Hazard: `hazard_score`
- Burden: `LiveDeficit_lag6`
- Recovery: `RecoveryWeakness_v1_lag6`, `RecoveryWeakness_v1_mean24`, `RecoveryWeakness_v1_delta24`
- Persistence: `episode_age_log`, `episode_age_sat`, `episode_starts24`, `episode_starts48`
- Trajectory: `SimpleShock_mean24`, `hazard_score_mean6`

## Frozen 2024 results

| Model | ROC AUC | PR AUC | Brier | Log loss | Calibration MAE |
|---|---:|---:|---:|---:|---:|
| Hazard | 0.8929 | 0.0423 | 0.00778 | 0.04647 | 0.0163 |
| Hazard + Burden | 0.9174 | 0.0446 | 0.00776 | 0.04544 | 0.0169 |
| Hazard + Burden + Recovery | **0.9274** | **0.0479** | **0.00770** | 0.04676 | 0.0181 |
| Hazard + Burden + Recovery + Persistence | 0.9241 | 0.0460 | 0.00771 | 0.04749 | 0.0171 |
| Hazard + Burden + Recovery + Persistence + Trajectory | 0.9128 | 0.0419 | 0.00774 | 0.04802 | 0.0176 |
| Hazard + Trajectory | 0.9151 | 0.0412 | 0.00783 | 0.04631 | 0.0160 |
| Burden only | 0.8782 | 0.0327 | 0.00783 | 0.04768 | 0.0181 |
| Recovery only | 0.7369 | 0.0148 | 0.00794 | 0.05352 | 0.0218 |
| Persistence only | 0.7403 | 0.0704 | **0.00767** | 0.04850 | **0.0123** |
| Trajectory only | 0.9131 | 0.0407 | 0.00785 | 0.04636 | 0.0160 |

## Paired bootstrap delta-AUC on 2024

1,000 paired resamples of the 2024 holdout:

- Burden addition: `A+B − A`: mean +0.0245, 95% interval [+0.0024, +0.0519]
- Recovery addition: `A+B+R − A+B`: mean **+0.0100**, 95% interval [+0.0060, +0.0144]
- Persistence addition: `A+B+R+P − A+B+R`: mean **−0.0033**, 95% interval [−0.0074, +0.0006]
- Trajectory addition after all prior heads: `A+B+R+P+T − A+B+R+P`: mean **−0.0113**, 95% interval [−0.0155, −0.0076]
- Hazard + Trajectory vs Hazard: mean +0.0222, 95% interval [−0.0035, +0.0518]

## Interpretation

### Hazard
Hazard is a real independent information channel in the broader architecture, but in this Crash72 court it is better viewed as a state/severity input than a calibrated crash probability by itself.

### Burden
Burden adds independent ranking information beyond Hazard on the frozen 2024 holdout. Its marginal representation is therefore not redundant with Hazard.

### Recovery
Recovery adds a reproducible ranking lift after Hazard + Burden. The lift is positive in paired bootstrap testing. However, its current representation slightly worsens log loss/calibration error relative to the smaller model. The conclusion is **keep Recovery as a candidate head, but do not promote the current formula as final**.

### Persistence
Persistence does not demonstrate a positive incremental AUC contribution after Hazard + Burden + Recovery. Its addition slightly reduces AUC and worsens log loss. The current persistence representation is therefore a **merge/rebuild candidate**, not an independent head.

### Trajectory
The current Trajectory representation does not add information after the other heads in this Crash72 court; its conditional addition materially reduces AUC and PR AUC. This does **not** prove that temporal direction is useless. It proves that the current two-feature Trajectory representation is not the right incremental channel in this target/context.

## Architectural verdict

Do not yet lock Hydra at five heads.

The evidence currently supports:

1. Hazard — retain.
2. Burden — retain.
3. Recovery — retain as an experimental independent channel; improve representation/calibration.
4. Persistence — **do not promote** in current form; search for a genuinely independent history state or merge it.
5. Trajectory — **do not promote in current form for Crash72**; re-test on a transition target where direction is actually the job.

The next maximum-discrimination experiment is therefore a **Recovery representation search conditioned on Hazard + Burden**, plus a separate **Trajectory court using next-state transition labels rather than Crash72**. Persistence should be challenged with the same conditional-emergence procedure before it is deleted.

## Status

This is an empirical result from the supplied canonical CSV. It is not yet a canonical Hydra architecture decision.
