# Platform Core v2.37.0.1 — Causal Migration Metadata & Tag Identity Repair

This patch keeps the v2.37.0 Causal Systems Explorer capability unchanged while repairing production deployment mechanics.

- Migration head remains `0041`.
- `0041` description is shortened below the production `schema_migrations.description VARCHAR(300)` limit.
- A failed v2.37.0 deployment may leave all seven causal tables created while `0041` is absent from `schema_migrations`; this state is explicitly recognized and safely recoverable.
- Promotion refuses to reuse an existing `v2.37.0.1` tag and verifies the new tag points to the promoted HEAD.
- The deployed v2.36.1.2 uncertainty schema and migration `0040` remain untouched.
