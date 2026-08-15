# v2.17.0 Production Certification Audit

Release gates cover migration head, zero pending migrations, database round-trip, governance audit-chain integrity, recovery-checkpoint integrity, optional required first-party gateway readiness, and non-blocking external provider health.

Recovery checkpoints do not contain database contents and cannot replace an external backup.
