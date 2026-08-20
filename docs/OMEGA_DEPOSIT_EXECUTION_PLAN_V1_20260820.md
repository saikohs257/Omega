# OMEGA — DEPOSIT EXECUTION PLAN V1

## Objective

Get the complete accessible Omega system into durable GitHub storage, then prove completeness.

## Phase 1 — control plane (implemented)

- full-system manifest
- alias/term index
- deposit protocol
- completion standard
- deposit queue
- source map
- audit script
- manual audit workflow
- system-layer architecture
- Senate/Blackadder/Seam/Hinge contract
- reconstructed Senate spine
- reconstructed Blackadder spec
- negative-knowledge ledger

## Phase 2 — exact source reconciliation

For every item in the remaining external artifact queue:

1. locate exact source in File Library / historical archive;
2. compare filename/content against repository;
3. compute SHA256 when raw bytes are available;
4. deposit exact bytes under `archive/source/`;
5. add source-map entry;
6. rerun repository audit.

## Phase 3 — canonicality audit

For every subsystem:

- identify current canonical implementation;
- mark all prior implementations superseded or archive-only;
- identify research-only components;
- identify annotation-only components;
- identify missing exact builders.

## Phase 4 — executable verification

Manual workflows verify:

- repository revision
- manifest completeness
- source presence
- code importability
- schema validity
- core tests
- restoration/provenance contracts

## Phase 5 — freeze

Write a final:

`OMEGA_FULL_SYSTEM_DEPOSIT_VERDICT_<date>.md`

with counts for:

```text
CANONICAL
ACTIVE_RESEARCH
SHADOW
ANNOTATION_ONLY
AUDIT_ONLY
SUPERSEDED
ARCHIVE_ONLY
MISSING_SOURCE
```

No unresolved memory-only subsystem remains after freeze.

## Storage rule for large raw archives

Keep exact source archives separate from normal runtime code. Use a Git-compatible large-file storage mechanism when the raw artifact is too large for ordinary repository blobs; do not rewrite or recompress evidence merely to make the deposit fit.

## Why this plan

The objective is not to make the Git tree look tidy. The objective is to make the entire system recoverable, attributable, and auditable from GitHub without depending on chat memory.
