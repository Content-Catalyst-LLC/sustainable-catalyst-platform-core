# Platform Core v2.23.1 — Capability Metadata, Documentation & Release-Lineage Repair

v2.23.1 is a truth and promotion-lineage repair on top of v2.23.0. It does not add a database migration or change Federated Core behavior.

## Repaired

- Runtime version, public SDK versions, WordPress plugin version, Render user agent, README, roadmap, changelog, deployment tooling, and release artifacts are aligned to `2.23.1`.
- `/v1/meta` no longer incorrectly marks `distributed_connector_workers` and `server_sent_live_data_events` as deferred.
- SDK documentation lineage labels for distributed scale, governance, production certification, and observability now point to their actual introduction releases.
- A new release-lineage regression suite prevents implemented/deferred overlap and checks static implementation evidence for the two repaired capabilities.

## Preserved

- Migration head: `0026`.
- No `0027` migration.
- v2.23.0 federation semantics and trust boundaries.
- Existing routes and schemas.
- Evidence and provenance semantics.
- Public/private visibility boundaries.

Next planned feature release: **v2.24.0 — Capacity Forecasting & Resource Governance**.
