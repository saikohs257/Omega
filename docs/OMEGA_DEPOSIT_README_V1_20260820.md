# Omega Full Deposit — Operating README

The repository is the durable memory of the system. Conversation is not a source of authority.

## What belongs here

- executable implementations
- schemas/contracts
- canonical data and fixtures where size/provenance permit
- experiment code
- experiment results
- architecture/handoff documents
- historical source artifacts or cryptographic references to them
- negative knowledge
- audit and reconciliation tooling

## What does not belong here as authority

- unsupported claims
- silently reconstructed source presented as exact recovery
- stale code with no status label
- untraceable numbers
- future-derived fields in past-decision datasets

## Recommended flow

```text
File Library / historical archive
        |
        v
source identification
        |
        v
byte-preserving deposit when possible
        |
        +---- exact source --> archive/source
        |
        +---- reconstructed --> archive/reconstructed
        |
        +---- current canonical --> runtime / omega / bentaxis / experiments
        |
        v
manifest + provenance + audit
        |
        v
manual workflow verification
```

## Completion state

The full-system deposit is complete only when the Deposit Audit Queue has no unexplained entries and every subsystem has an explicit status.
