# Datanet DT-1 → Omega ingestion contract

Status: recovery/integration contract. No synthetic market data is permitted.

## Boundary

Datanet Mobile is the evidence acquisition surface. Omega consumes exported, replayable `formal_field_packet` snapshots; Omega does not treat Datanet scores as predictions or authority.

```text
Datanet
  acquire -> validate -> normalize -> archive -> export
                         |
                         v
                formal_field_packet
                         |
                         v
                 Omega CorpusSnapshot
                         |
              chronological holdout
                         |
             +-----------+-----------+
             |           |           |
          Control A   Control B   A / B / A×B
             |           |           |
             +-----------+-----------+
                         v
              ProbabilityContract
                         |
                  AUC / Brier / LL
                         |
                 calibration report
```

## Required packet identity

- `schema_version`
- `producer`
- `producer_version`
- `asset`
- `quote`
- `timestamp_utc`
- `snapshot_id`
- `authority_cap`
- source-contract block

## Evidence requirements

`minimum_evidence.pass` and its reason must be retained. `direct_sources` are evidence; `consensus` is derived cross-source evidence; `_PROXY_` fields remain explicitly heuristic; `context_only` fields never create core steering authority.

Missing values remain `null`, never zero. Field confidence describes source reliability, not predictive truth.

## Network-truth rules

Cached data may support diagnostics but cannot be promoted to live market truth. A failed minimum market spine must remain a degraded/blocked observation rather than becoming a fabricated predictor row.

## Replay requirements

Omega must retain the original snapshot identity and timestamp. Any downstream transformation must be deterministic and provenance-linked to the source snapshot. Chronological train/validation/test boundaries must be established before fitting or selection.

## Probability boundary

Only candidates that satisfy Omega's probability contract may enter AUC/Brier/log-loss/calibration scoring. A historical or non-probabilistic controller is recorded as `INCOMPARABLE`, not adapted solely to obtain a probability score.

## Benchmark matrix

The real benchmark should contain exactly the agreed honest comparison:

- Control A
- Control B
- A
- B
- A×B

No synthetic market values, invented labels, post-hoc probability conversion, or control inflation.

## Current blocker

This contract does not claim that historical Datanet snapshots are present in the Omega repository. The next ingestion step is to locate/recover the archived snapshot corpus from the Datanet/oracle-surface-mobile lineage, verify hashes/provenance, and then build the Omega `CorpusSnapshot` fixture from those real artifacts.
