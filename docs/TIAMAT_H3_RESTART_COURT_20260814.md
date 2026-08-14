# TIAMAT H3 Restart Court — 2026-08-14

## Basis

Canonical `layer1_structured_hazard_arm_timeseries(15).csv`, 43,848 hourly rows, 2020-2024.

This document is a clean restart of H3 reconstruction. It separates native observations from reconstructed controller logic.

## Test 1 — H3 population

`entry_path == 3_to_4` contains 1,021 hourly rows and 169 episode starts.

At H3 episode starts:
- trapped: 7
- phasic: 137
- mixed: 25

## Test 2 — Hard trapped boundary

Candidate `hazard_score >= 0.966` is the documented H3 hard boundary.

On the 169 native H3 starts:
- predicted trapped rows: 11
- exact classification accuracy: 0.9408
- false positives: 7
- false negatives: 3

The boundary is therefore a real branch in the recovered controller, but `0.966` alone is not sufficient to reproduce all native episode-type labels.

For comparison:
- 0.9526 -> 0.9349 accuracy
- 0.975 -> 0.9822 accuracy, but misses 3 trapped cases

Do not replace the recovered 0.966 hard branch with a fitted threshold; the recovered tracker explicitly uses 0.966 as the trapped boundary, and the remaining classification is handled by the phasic/mixed branch.

## Test 3 — Non-hard H3 branch

Restricting to starts with `hazard_score < 0.966` leaves 158 starts:
- phasic: 137
- mixed: 18
- trapped: 3

Single-feature AUC for identifying phasic:
- current SimpleShock: 0.3872
- recent hazard peak (6h): 0.4129
- episode starts in prior 24h: 0.6587
- episode starts in prior 48h: 0.6722

This is strong evidence that **recent episode tempo/history** carries more H3 branch information than raw instantaneous shock or burden.

## Test 4 — Reconstructed phasic score without volume

Using the recovered tracker scoring structure, but omitting the unavailable daily volume-expansion term:

- `+2` when shock <= 0.70
- `+1` when recent hazard peak > 0.80
- `-1` when shock > 0.80
- `+4` when >=3 episode starts in the prior 24h and shock <= 0.70
- else `+3` when >=4 starts in prior 48h and shock <= 0.70
- phasic when score >= 1

Results on the 158 non-hard H3 starts:
- exact phasic/mixed agreement: 84.81%
- phasic recall: 94.89%
- false phasic classifications: 17

This is a reconstruction, not canonical authority, because the documented tracker also uses a 5-day volume-expansion term that is not present in the canonical Layer-1 CSV.

## Interpretation

The restart weakens the earlier hypothesis that H3 is primarily a continuous `LiveDeficit - SimpleShock` classifier.

The cleaner picture is:

```text
3_to_4 entry
   |
   +-- hazard_score >= 0.966 -> hard trapped branch
   |
   +-- otherwise -> phasic/mixed classifier
                         |
                         +-- recent episode tempo/history is important
                         +-- shock level modifies the interpretation
                         +-- recent hazard peak supplies context
                         +-- daily volume expansion is an additional documented term
```

## Falsified / downgraded hypotheses

1. H3 is a simple raw-`LiveDeficit` threshold: not supported.
2. H3 is fully explained by current shock: contradicted by low AUC.
3. H3 is fully explained by recent hazard peak: contradicted by low AUC.
4. The earlier proxy `BURDEN x HAZARD` result is not native authority; prior native leakage-clean work already showed that effect did not survive.

## Next discriminatory experiment

Recover or align the daily volume source used by `gate_3to4` and replay the **exact** phasic score against the 169 native H3 starts. Then perform single-component ablations:

1. tempo removed
2. shock terms removed
3. hazard-peak term removed
4. volume-expansion term removed

The winning explanation must reproduce native phasic/mixed labels out-of-sample without using `episode_type` or `duration_bucket` as inputs.
