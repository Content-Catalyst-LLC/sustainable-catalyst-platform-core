# Cross-Product Evidence Exchange — v2.14.0

Platform Core v2.14.0 establishes a governed handoff contract across Sustainable Catalyst products.

## Design invariants

- Handoffs are reference-first and non-destructive.
- Canonical Core subjects remain the source of record.
- A receiving product may acknowledge or derive from a package without rewriting the source artifact.
- Exchange metadata never creates factual Truth precedence. Each item inherits the authority of its canonical subject.
- Private/non-public subjects cannot be promoted into public exchange packages.
- Secret-bearing snapshots or provenance metadata are rejected before persistence.
- Automatic cross-product delivery is disabled in v2.14.0; packages use pull/acknowledgement semantics.
- Package creation is idempotent per origin, target, and idempotency key.

## Supported product identities

Site Intelligence, Workspace, Lab, Knowledge Library, Decision Studio, Research Librarian, Workbench, Advisory, Catalyst Data, Finance, and Narrative Risk.

## Supported canonical subjects

Entities, claims, evidence records, source snapshots, live observations, scientific and economic records, international-law records, geospatial features, time series, scientific assets, map layers, facilities and facility observations, humanitarian conditions, country reconciliation records, and scientific domain bindings.

## Privacy boundary

Package contents are an internal authenticated Core surface. The public API exposes readiness/capability metadata only and never lists exchange package contents.
