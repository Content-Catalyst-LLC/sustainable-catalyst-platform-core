# v2.22.0 Data Lifecycle & Preservation Audit

## Invariants
- Lifecycle hard delete is disabled.
- Holds block tombstone actions.
- Archives are content- and manifest-hashed with SHA-256.
- Archive restoration records a reference-first restore action and does not overwrite canonical source truth automatically.
- Credential-like metadata is redacted before persistence.
- Lifecycle does not change evidence authority or Truth precedence.
