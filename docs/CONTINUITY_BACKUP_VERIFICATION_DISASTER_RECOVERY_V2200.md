# Core v2.20.0 — Continuity, Backup Verification & Disaster Recovery

Core v2.20.0 adds a governed continuity plane over the recovery metadata introduced in v2.17.0.

## Boundaries

- Recovery checkpoints remain metadata/integrity records; they are not database backups.
- Core does not persist backup credentials.
- Core does not execute arbitrary restore shell commands.
- Automatic database restore is disabled.
- Filesystem verification is constrained to `SC_CORE_BACKUP_FILESYSTEM_ROOT`.
- SQLite backups can be restored into a temporary isolated database for a real integrity rehearsal.
- PostgreSQL and other production restores remain externally executed and are recorded as structured attestations with evidence.
- RPO/RTO and continuity status have no evidence authority and cannot alter provenance or domain truth.

## Certification integration

`SC_CORE_CERTIFICATION_REQUIRE_RECENT_VERIFIED_BACKUP` and `SC_CORE_CERTIFICATION_REQUIRE_RECENT_RESTORE_REHEARSAL` are opt-in gates. They default false to avoid blocking initial deployment before an operator has registered production backup infrastructure.
