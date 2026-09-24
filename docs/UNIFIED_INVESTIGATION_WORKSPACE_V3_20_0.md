# Platform Core v3.20.0 — Unified Investigation Workspace

This release adds a governed investigation container that unifies existing Core evidence, forensics, visual-reasoning, predictive, and reproducibility capabilities without replacing their specialist object models.

## Core contract
- Investigation manifest with title, domain, status, and object inventory.
- Cross-domain object references with provenance payloads.
- Explicit directed relationships with rationale and optional 0–100 confidence.
- Named analytical views stored as specifications.
- Investigation map endpoint returning nodes, edges, and views.
- Integrity diagnostics for dangling relations and object-type counts.
- Immutable canonical JSON snapshots with SHA-256 identity.
- Cross-product handoff bundles for Research Lab, Knowledge Library, Workbench, Decision Studio, Site Intelligence, or other Catalyst applications.

The layer is additive: existing Core evidence and research objects remain authoritative. The workspace stores references and investigation context rather than duplicating or silently rewriting those objects.
