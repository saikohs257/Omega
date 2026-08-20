# OMEGA DEPOSIT COMPLETION STANDARD V1

## Definition of complete

The system is not "all in GitHub" because many files exist. It is complete when the following assertions pass.

### A. Identity
Every subsystem has an explicit canonical name and alias map.

### B. Provenance
Every source-bearing artifact has origin/date/version metadata or is explicitly marked reconstruction.

### C. Authority
Every component is labeled by authority class: canonical, promotable, diagnostic, annotation, shadow, reserve, superseded, or archive-only.

### D. Reproducibility
Every important result has executable code or an explicit source-package reference sufficient to reconstruct it.

### E. Negative knowledge
Failed candidates and demoted rules remain discoverable.

### F. Metric contracts
AUC, PR-AUC, Brier, log loss, calibration, and complexity all have explicit direction/interpretation rules.

### G. Workflow reproducibility
Manual research workflows verify requested revision and checked-out SHA.

### H. Deposit audit
The repository audit has no unexplained source-queue entries.

## Final verification sequence

```text
1. run term/index audit
2. run source-name audit
3. reconcile File Library source queue
4. deposit exact bytes where available
5. label reconstructed material
6. run repository test suite
7. run manual archaeological/deposit workflow
8. inspect artifact + commit SHA
9. update this standard with final verdict
```

## Important distinction

`repository-complete` means the durable system map and all accessible authoritative sources are deposited.

It does not mean every ephemeral run artifact, cache, or external service state must be committed.
