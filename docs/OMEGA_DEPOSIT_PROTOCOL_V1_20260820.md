# OMEGA — DEPOSIT PROTOCOL V1

## Objective

Move the complete reconstructed system from conversation/file-library archaeology into GitHub without collapsing generations, overwriting truth, or mixing archive evidence with live authority.

## Deposit classes

### 1. Source
Exact code/data/document bytes from a historical package.

### 2. Reconstruction
A newly recreated implementation whose exact original bytes are unavailable.

### 3. Canonical
Current implementation explicitly designated authoritative.

### 4. Evidence
Results, ledgers, tables, reports, run artifacts, or proof records.

### 5. Archive
Superseded or historical material preserved solely for lineage/replay.

## Directory convention

```text
/archive/
  source/<project>/<dated-package>/
  reconstructed/<project>/<dated-reconstruction>/

docs/
  architecture/
  handoffs/
  findings/
  governance/

experiments/
  <experiment-code>
  results/

data/
  canonical/
  derived/
  fixtures/

contracts/
  schemas/

runtime/
  core runtime machinery

bentaxis/
omega/
```

Do not move existing files merely for aesthetics. Existing paths are provenance. Add index files where a migration would be disruptive.

## Per-artifact metadata

Every newly deposited historical artifact gets a sidecar or catalog row containing:

```text
artifact_id
original_name
repository_path
source_origin
source_date
retrieval_date
sha256_if_available
status
project
subsystem
supersedes
superseded_by
canonicality
notes
```

## Rules for reconstructed code

Never present reconstructed code as recovered source.
Use:

`RECONSTRUCTED_FROM_MEMORY`

or

`RECONSTRUCTED_FROM_DOCUMENTED_SPEC`

until byte-level provenance is available.

## Rules for results

A result record must identify:

- target
- data source
- feature source
- estimator
- temporal protocol
- label construction
- metric definition
- metric polarity
- exclusions
- seed if stochastic
- commit SHA

## Rules for negative knowledge

Do not delete because a signal failed.
Do not delete because a role was demoted.
Do not delete because a theorem was superseded.
Record why it lost authority.

## Rules for workflows

Research and archaeology workflows are `workflow_dispatch` only unless explicitly promoted to ordinary CI.
Every manual research workflow must print:

```text
requested_ref
GITHUB_SHA
checked_out_SHA
experiment_identifier
```

and fail if the checked-out SHA differs from the requested revision.

## Completion criterion

The deposit is complete when the repository audit reports zero `MISSING_SOURCE` items for the known source queue, or every remaining item has an explicit `ARCHIVE_ONLY_EXTERNAL` status with a documented external source.

## Atomicity

Prefer one atomic Git commit per coherent deposit batch. Use repository tree/commit APIs for large batches so the index and artifacts arrive together.

## Do not silently reconcile

If two historical sources disagree:

1. preserve both;
2. label the conflict;
3. identify which is currently canonical;
4. create a reconciliation document;
5. never edit the older artifact to match the newer one.
