# v2.41.0 Audit

- Migration 0045 additive only.
- Requires complete v2.40.0 cross-product visual research schema.
- Inputs preserve source-product identity, explicit references, versions, hashes, and provenance.
- Environments capture runtime/dependency/container/code/seed context.
- Replay plans are external-only and reject Core-side specialist execution.
- Core integrity verification is distinct from external output equivalence.
- Snapshots are immutable and SHA-256 identified.
- Automatic truth promotion remains disabled.
