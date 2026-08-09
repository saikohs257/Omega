# E.N.D. + Darwin's Pond — Frozen Architecture V1

> Status: frozen conceptual architecture. This document is an implementation target and provenance layer, not runtime authority.

## 1. Scope

E.N.D. (Enhanced Failure-Diagnosis) is Omega's immutable failure-analysis layer.
Darwin's Pond is Omega's immutable hypothesis-lineage reservoir.

They sit beside TIAMAT, not inside TIAMAT's state machine.

- TIAMAT: structural dynamics, state evolution, guards, transitions, prediction surface.
- E.N.D.: failure interpretation, taxonomy, certainty, counterfactual diagnosis.
- Darwin's Pond: bounded mutation proposals, lineage, quarantine, resurrection, historical memory.

## 2. Non-negotiable principles

1. Evidence is immutable.
2. Historical hypotheses are immutable.
3. Diagnoses are versioned and revisable.
4. Failure never silently disappears.
5. Diagnosis is not causation.
6. Mutation is precommitted before execution.
7. New descendants always receive new identities.
8. The test spine is not evolutionary training material.
9. UNKNOWN is a valid outcome.
10. E.N.D. diagnoses; Darwin's Pond generates bounded descendants.

## 3. Layer separation

### E.N.D.
Analytic only.

Questions it may ask:
- What failed?
- Under what conditions did it fail?
- Which evidence supports the diagnosis?
- Is the failure structural, dynamic, temporal, statistical, data-related, experimental, implementation-related, or unknown?
- Is the causal status unknown, correlated, suspected, or confirmed?

Questions it may not answer by fiat:
- What should be mutated?
- What should be retried automatically?
- What is the winning descendant?

### Darwin's Pond
Generative but bounded.

Questions it may ask:
- Which single mutation is authorized?
- Should the failed hypothesis be snipped, altered, or held?
- Is this lineage quarantined?
- Is resurrection justified under changed assumptions?

Questions it may not answer by itself:
- What is the correct diagnosis?
- Whether the failure was real.
- Whether the current hypothesis should be rewritten in place.

## 4. FailureRecord

Every failure should create a content-addressed immutable failure record.

Required fields:
- failure_id
- experiment_id
- hypothesis_id
- corpus_hash
- information_set_hash
- metric_contract_hash
- implementation_hash
- outcome
- metrics
- residuals
- stratum_results
- reliability_results
- failure_taxonomy
- certainty_level
- created_at

A sealed FailureRecord is immutable.

## 5. Failure taxonomy

Supported taxonomy buckets:
- structural
- dynamic
- temporal
- statistical
- data
- experimental
- implementation
- unknown

The taxonomy is intentionally conservative.
E.N.D. should prefer UNKNOWN over speculative overreach.

## 6. Certainty levels

- UNKNOWN
- CORRELATED
- SUSPECTED
- CONFIRMED

Rules:
- CORRELATED means repeated association without resolved causality.
- SUSPECTED means mechanism-plus-evidence points strongly in one direction.
- CONFIRMED means a controlled counterfactual or equivalent evidence supports the claim.
- UNKNOWN is always allowed.

## 7. Mutation operations

Initial allowed operations:
- SNIP: remove one suspected component.
- ALTER: change one identified component.
- HOLD: do nothing.

MERGE is explicitly deferred.

All mutation proposals must be precommitted with:
- source hypothesis
- source failure
- diagnosis reference
- operation
- target component
- rationale
- expected effect
- created-before-execution marker

## 8. Lineage rules

- A descendant is always a new hypothesis with a new identity.
- The parent remains unchanged.
- Every mutation produces a fresh lineage node.
- Mutation budgets are finite.
- Exhausted lineages may be quarantined.
- Quarantine means not active, not mutating, not erased.

## 9. Safety and governance rules

E.N.D. and Darwin's Pond must never:
- modify evidence
- rewrite historical hypotheses
- access the untouched test spine as training material
- auto-mutate after failure
- silently discard failure history
- collapse diagnosis into causation
- bypass provenance
- recursively diagnose themselves

## 10. First implementation target

The first concrete implementation should provide:
- immutable failure records
- controlled taxonomy
- certainty levels
- mutation proposals
- lineage tracking
- quarantine status
- explicit HOLD behavior
- explicit UNKNOWN behavior

No automatic optimizer loop is allowed in V1.

## 11. Relationship to TIAMAT

TIAMAT produces structural state and transition behavior.
E.N.D. interprets TIAMAT failures.
Darwin's Pond preserves and proposes descendants for TIAMAT hypotheses.

This separation protects TIAMAT history while allowing disciplined evolution of descendants.
