# TIAMAT Research Source Ledger V1

This ledger records the external TIAMAT handoff packages used to construct `TIAMAT_RESEARCH_CANON_V1`. These artifacts are evidence/research inputs, not runtime authority.

| Artifact | SHA-256 | Role | Status |
|---|---|---|---|
| `hf9_tiamat_calibration_v3_handoff_20260611.zip` | `5b5f683e663d07a126ef7a9591b79677df1e98d2982c84e6968838bc966a3a66` | Head-local/global calibration doctrine | RESEARCH / SHADOW |
| `hf9_tiamat_v21_2_top_bad_run_visual_forensics_v1_20260614.tar.gz` | `0f1489bf337bb1fdd30fcedeb3c421c5f09d63c3353cb60a82b1ef14ba38cc0f` | Bad-run forensic evidence and no-patch findings | RESEARCH |
| `TIAMAT_A_CHUG_ROUTER_HANDOFF_20260702.tar.zst` | `39d1f4d25ef2046cbd0e022865f4f89aea1f3443ca6a99d797bbfe613700a53b` | Route/current/charge/exit court evidence | RESEARCH / INTEGRITY WARNING |
| `TIAMAT_AMP_CURRENT_RESEARCH_HANDOFF_20260625.tar.zst` | `7d9f346a9f915005e583ff5f602305438fe5319a8bb9f501e922425eaf2365e8` | Conditional current/conductance findings | RESEARCH / GLOBAL PROMOTION BLOCKED |
| `TIAMAT_AMPVEC_DICTIONARY_FOCUS_V0_20260624.tar.zst` | `0b7337eeb1e73ba820390af56f7efedb76232a69e3c3cf0c50b4939cb3b0c732` | Dictionary, placement, vector-pull vocabulary | RESEARCH / CRASH LANE BLOCKED |
| `TIAMAT_AUTHORITY_ENGINE_RC3_STRICT_WORKING_20260625.tar-3.zst` | `6c84dbc9f6161509b6f0d709b1d418bd575c7cfc20eef9635c6ac723cae9647c` | Authority/conflict court implementation research | RESEARCH / RUNTIME BLOCKED |
| `TIAMAT_AUTHORITY_RESEARCH_FULL_LEARNING_HANDOFF_20260625.tar.zst` | `9ca53ca9658a63f821c72de7b0296de4354b96328c852ad761de8a7ab9b9fccb` | Canonical lessons and independent-spine requirements | RESEARCH / CANON INPUT |
| `TIAMAT_CONTINUATION_ANALYSIS-2.md` | `4abf993704c2c3d98c6c72e19d325b54fdb5d7d5dbe81720dfe2d9c251dd9d16` | Falsification roadmap, ablations, Kalman/null comparison | RESEARCH / VALIDATION ROADMAP |
| `TIAMAT_FALSE_WATCH_GRAMMAR_28STEP_SOLUTION_20260625.tar.zst` | `067b105bec2a0dfe8318da44c0f3a141c07055549d3ea732e7481b352f056612` | False-watch grammar, causal order, alert budget, conflict logic | RESEARCH / RUNTIME BLOCKED |
| `TIAMAT_PROOF_MODE_HANDOFF_RECENT_RESEARCH_20260628.tar-1.zst` | `88cc87be99ccc80b0a56df3cfe0d9da792c7ded71f57d9b1beff53eee46635af` | Proof-mode/recent research continuation | RESEARCH |

## Integrity note

`TIAMAT_A_CHUG_ROUTER_HANDOFF_20260702.tar.zst` currently fails `unzstd -t` with a premature-EOF error. Its SHA-256 above identifies the uploaded bytes, but the archive must not be treated as a complete extractable source until a verified copy is supplied. Partial contents may be inspected only as explicitly marked inspection evidence.

## Authority rule

A source artifact may establish a research claim, formula candidate, or implementation requirement only at its declared research status. No artifact in this ledger grants runtime authority, probability authority, or global burden authority.

## Evidence promotion rule

Before a claim moves from research to canonical experiment input, record:

```text
claim_id
source_artifacts
source_hashes
gate_status
authority_status
independent_replay_status
```

This ledger is intentionally conservative: provenance is preserved even when the underlying claim is blocked or contradicted by later evidence.
