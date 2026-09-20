# Platform Core v2.79.0 — Research Argument & Evidentiary Synthesis Engine

Platform Core v2.79.0 adds a provenance-aware layer for assembling researcher-authored arguments and evidentiary syntheses from the structured research objects introduced in v2.72–v2.78.

## Added

- Governed research argument registry.
- Typed argument nodes for evidence, findings, interpretations, claims, hypotheses, assumptions, counterclaims, limitations, context, and methods.
- Explicit researcher-declared argument edges such as `supports`, `contradicts`, `qualifies`, `depends_on`, `contextualizes`, `responds_to`, and `derived_from`.
- Researcher-authored evidentiary synthesis records and source components.
- Counterargument and unresolved-tension registries.
- Descriptive argument-map coverage summaries.
- Argument revision history and immutable hash-chained snapshots.
- Public bundle/map surfaces for public research projects.
- WordPress status surface and public Python/JavaScript SDK helpers.
- Migration 0083 and partial-migration recovery validation.

## Research boundary

Core stores and traces declared scholarly reasoning. It does not generate arguments or syntheses, infer support relations, score evidence, rank or select arguments, resolve evidentiary tensions, infer truth, or publish autonomously.
