# Omega Canonical Architecture and Dataflow V2

> Status: architecture reconciliation draft with Gate B evidence/result boundary frozen.

## Gate B boundary

```text
CorpusIdentity -> InformationSet -> ExperimentSpec -> ProvenanceManifest -> ExperimentResult
```

Every result is bound to the exact experiment identity and manifest identity. Result scope is explicit: `development`, `validation`, `holdout`, or `test`.

Only an explicitly `test`-scoped `ExperimentResult` may enter the final test spine. Development, validation, and holdout results cannot claim test authority through the result boundary.

## Core organism

Constitution -> Identity -> BentAxis -> Colony -> Runtime -> Evidence -> Experiment -> Atlas/TESSERACT -> Hypergraph -> Simplicial -> Sheaf -> TIAMAT -> ERK/Oracle -> Court -> E.N.D. -> Darwin's Pond -> bounded mutation -> L0 -> holdout/test firewall -> authority.

## TIAMAT

TIAMAT is the structural-dynamics layer. Its canonical runtime surface is:

- seven legal modes Q/P/E/C/H/R/Rf;
- M3 primary state `[B,V,D]`;
- optional `tau_D`, `tau_mode` temporal memory;
- recovery, pressure, momentum, residual-load derived observables;
- explicit guard evaluation and precedence;
- legal transition table;
- shared live/replay transition logic;
- canonical state projection;
- M0-M7 identification registry with M7 permanent control.

TIAMAT must not be reduced to a probability scalar, and identification must not become a second runtime.

Historical concepts such as SimpleShock, LiveDeficit, RecoveryWeakness_v1, hazard_raw/hazard_score, hinge, richer damage/recovery/residual-load/momentum equations, refractory thresholds, promotion thresholds, and hysteresis remain evidence-classified until source provenance plus deterministic implementation/tests justify promotion. See `docs/TIAMAT_CLAIM_LEDGER_V1.md` and `docs/TIAMAT_RECONCILIATION_V1.md`.

## Verification order

1. Identity and canonical bytes
2. BentAxis provenance/history
3. Runtime replay determinism
4. Evidence/experiment/result boundary
5. Test-spine firewall
6. Atlas/Hypergraph/Simplicial/Sheaf
7. TIAMAT structural dynamics
8. ERK/Oracle/Court
9. E.N.D.
10. Darwin's Pond

## Research rule

Never replace a missing layer with a convenient approximation. Label partial, experimental, historical, or recovering concepts explicitly and preserve their provenance.
