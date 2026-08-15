# Platform Core v2.17.0 — Production Certification, Migration Assurance & Recovery Readiness

This release adds persisted production certification runs, migration assurance through schema head `0020`, recovery checkpoint metadata with SHA-256 integrity verification, and a public-safe readiness surface.

## Recovery boundary
A Core recovery checkpoint is metadata plus integrity evidence. It is **not** a database dump or substitute for an external PostgreSQL/host backup. Full restoration requires operator-managed backup media or a managed database snapshot.

## Certification policy
Zero pending migrations and a valid governance audit chain are required by default. First-party gateway readiness can be made certification-blocking with `SC_CORE_CERTIFICATION_REQUIRE_GATEWAY_RELEASE_READY=true`. Transient external data-provider health is never a release blocker.
