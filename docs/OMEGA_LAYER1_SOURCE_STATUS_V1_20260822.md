# OMEGA Layer1 Source Status V1

Date: 2026-08-22
Status: CANONICAL EVIDENCE STATUS

## Corrected evidence boundary

The exact historical Layer1 2020–2024 **output/spine is recovered** in the File Library and is byte-verified.

This must not be described as a missing Layer1 timeseries.

The exact native **generator/source implementation** remains unrecovered unless and until its original source bytes are located and verified.

Therefore the current state is:

| Artifact | Status |
|---|---|
| Layer1 2020–2024 exact timeseries | `RECOVERED_EXACT` |
| Layer1 schema | `RECOVERED_EXACT` |
| Layer1 native generator | `MISSING_SOURCE` |
| Reproduction/proxy builders | `RECONSTRUCTION_ONLY` |
| Exact output provenance | `VERIFIED` |
| Native generator provenance | `UNRESOLVED` |

## Verified output identity

```text
rows: 43848
columns: 15
range: 2020-01-01 00:00 → 2024-12-31 23:00
sha256: 6f0dc516fdf3313ab27a38d942504d073faccba4067877531b44c219c5e4b31a
```

## Rule

Do not reconstruct the native generator merely because it is absent. Use the exact recovered output as the historical ground-truth spine. Any generated extension beyond the recovered period remains explicitly `PROXY`, `RECONSTRUCTED`, or otherwise source-classified until native provenance is established.

## Consequence

The former statement "the exact Layer1 timeseries is missing" is obsolete. The accurate statement is "the exact Layer1 native generator is still missing; the exact 2020–2024 output is recovered and verified."
