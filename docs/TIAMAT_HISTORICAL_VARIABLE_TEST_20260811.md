# TIAMAT Historical Variable Test — 2026-08-11

## Status

**Historical artifact tested:** `hf9_tiamat_v21_hidden_pattern_full_completion_20260614`

Primary replay substrate:

`HIDDEN_PATTERN_AUDIT_ROW_SUBSTRATE.csv`

- 35,528 hourly rows
- 2020-01-01 through 2024-12-31
- 1,434 strict runs in the companion run ledger
- No literal canonical `B`, `V`, or `D` fields were found in the tested artifact

This report deliberately does **not** treat D/V/B as historical TIAMAT variables.

## What was tested

### Row-level directional target

Target: `actual_t3_direction_proxy` (`UPSHIFT_PROXY` vs `DRAIN_PROXY`), with missing targets excluded.

Chronological 70/30 split; no random shuffling.

| Representation | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| entry_livedeficit | 0.6166 | 0.5793 | 0.2340 |
| entry_ret24h | 0.4633 | 0.4494 | 0.2490 |
| entry_up_pressure_proxy | 0.6828 | 0.6417 | 0.2338 |
| live_up_pressure_proxy | **0.7391** | **0.6962** | **0.2085** |
| entry_live_pressure_delta_abs | 0.4845 | 0.4121 | 0.2491 |
| run_age_h_live | 0.5825 | 0.5787 | 0.2467 |
| all instantaneous variables | 0.7369 | 0.7137 | 0.2080 |
| causal within-run history only | 0.5340 | 0.5127 | 0.2663 |
| instantaneous + causal history | 0.7139 | 0.6432 | 0.2135 |

The history features were constructed only from prior observations within the same run. No future rows were used in the causal-history calculation.

### State-3 run-exit target

Restricted to 429 non-censored State-3 runs with exits `3_to_4`, `3_to_2`, or `3_to_0`. Target = upshift vs drain.

Chronological 70/30 split.

| Representation | ROC-AUC | PR-AUC | Brier |
|---|---:|---:|---:|
| entry_livedeficit | **0.8668** | 0.8035 | 0.1351 |
| entry_up_pressure_proxy | **0.8777** | 0.8454 | 0.1380 |
| entry_taker_buy_ratio | 0.7199 | 0.6765 | 0.2286 |
| all entry variables | **0.8879** | **0.8618** | **0.1299** |

A retrospective full-run summary using `last`/`mean` fields reached AUC 0.9978, but this is **not a predictive result** because those summary fields include information from the completed run. It is retained only as a leakage demonstration.

## Existing historical findings corroborated by the artifact

The included V2.1 synthesis reports that removing/demoting stale and unreliable steering rules improved row precision from 0.764 to 0.863 and run-normalized precision from 0.936 to 0.970, with no new sensors. This supports the interpretation that authority discipline and temporal freshness materially affect predictive behavior.

## Interpretation

1. **D/V/B are not historical TIAMAT variables in this artifact.** They remain diagnostic notation only unless an original artifact explicitly defines them.
2. Historical TIAMAT has real predictive signal in the observed variables. `live_up_pressure_proxy` is the strongest single row-level directional feature in this test.
3. Combining contemporaneous observed variables is useful: the row-level all-instantaneous model is competitive with the strongest single variable and has slightly better Brier score.
4. The simple causal-history construction tested here did **not** improve prediction. Therefore we cannot currently claim that generic accumulation is the source of TIAMAT's predictive power.
5. The State-3 run-exit experiment shows strong entry-time signal (AUC 0.8879 combined), but the sample is only 429 runs and must be treated as a diagnostic result rather than a final model-selection result.
6. Completed-run `mean`/`last` summaries are contaminated for forward prediction and must not be used as training features for a fair predictive benchmark.

## Next experiment

The next historical test should reconstruct the **actual causal state trajectory available at each hour**, using only fields that exist at that timestamp, and compare:

- instantaneous observed variables;
- causal rolling/decay features;
- explicit run-age/freshness features;
- interaction terms;
- the recovered V2.1 rule engine;
- and, only if an artifact defines them, any historical hidden-state variables.

No D/V/B substitution should be made unless an original TIAMAT artifact provides those variables.
