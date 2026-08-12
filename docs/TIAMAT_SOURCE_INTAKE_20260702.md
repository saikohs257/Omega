# TIAMAT Source Intake — 2026-07-02

Status: evidence ledger; not runtime authority.

## Newly supplied artifacts

### A_CHUG runtime handoff

SHA-256:
`f169cbaa962807a6f8e29e946f78564c827b0b64d3e9c85e5592f30b0a751a7f`

The archive is structurally readable and contains the reconstructed A-axis runtime draft, trace replay court, cell-fuse court, pocket router, age sidechain, and source packages.

Important declaration from the supplied runtime package:
- reconstructed runtime draft;
- real V10 source not used;
- real TIAMAT V10 logs not used;
- canon_final=false.

Therefore this package is preserved as research/reconstruction evidence, not canonical runtime source.

### A_CHUG pocket router court

SHA-256:
`653ba751ac86e93c902b973c6bdb2ca182dbd3bfb11ab8b13265a094c609241d`

The court reports a train-only B_age router and explicitly keeps it below canon promotion.

### archiveNew.zip

SHA-256:
`cf50d9ad6eed9e689299d69576c18da5d83157e4346ced3bd6b87f05d4343ec0`

The ZIP is readable and contains 16 A-axis research packages, including:
- age sidechain residual gate;
- cell-conditioned CHUG;
- CHUG pocket router;
- CHUG sidechain enter;
- circuit battery enter/exit;
- current validated CMRR cap;
- enter template match/simplification;
- event qualifier board;
- exit release latch;
- mute/recover 4CHUG stability;
- phase impedance discriminator/row autopsy;
- split enter/charge/exit/release;
- split-law next4 handoff/row autopsy.

This complete readable bundle is the preferred source for these A-axis research packages over any truncated duplicate.

## Evidence interpretation

The supplied A-axis material contains a coherent progression:

```text
baseline
  -> split ENTER/EXIT law
  -> EXIT release latch
  -> template/circuit/phase research
  -> CHUG mute/recover family
  -> B_age pocket routing
  -> fatal-pocket cell fuse
  -> reconstructed runtime draft
  -> exact trace replay
```

The strongest reconstructed result is the age-addressed CHUG router with cell-fuse fallback, but it remains a reconstructed candidate rather than canonical TIAMAT runtime.

## Non-obvious architectural finding

The event-qualifier and template courts report that additional recovered ENTER rows can arrive with many more HOLD0 false rows. The supplied event-qualifier report explicitly interprets this as evidence for a missing coordinate such as arrival/age/timing rather than simply another same-channel analog feature.

The later CHUG pocket court independently finds that B_age changes which chug mode is useful:

```text
B_age=0 -> HOT recovery-biased
B_age=1 -> PREC precision/mute
```

This supports treating age/timing as a routing coordinate rather than multiplying global head strength.

## Hard boundary

Exact replay of a reconstructed runtime proves implementation reproducibility of that reconstruction. It does not prove that the reconstruction is the original TIAMAT controller.

No artifact in this intake may silently upgrade `real_v10_source_used=false` or `real_tiamat_v10_logs_used=false` into a true value.
