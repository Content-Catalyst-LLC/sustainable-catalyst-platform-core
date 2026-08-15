# v2.20.0 Continuity & Disaster Recovery Audit

- Backup credentials are not persisted.
- Credential-like metadata keys are redacted.
- Filesystem reads are limited to the configured backup root.
- Backup integrity uses SHA-256.
- SQLite restore rehearsals are isolated and non-destructive.
- PostgreSQL/remote restore execution is external-operator only.
- Automatic database restore is false.
- Arbitrary restore commands are unsupported.
- RPO/RTO are operational signals only and have no evidence authority.
- Certification backup/restore gates are opt-in.
