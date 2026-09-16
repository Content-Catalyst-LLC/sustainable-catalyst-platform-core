# v2.64.0 Linked Views & Cross-Filtering Audit

## Governed registries

- Link policies bound to a v2.62 view composition or link group.
- Selection sets with explicit source and target views.
- Declarative cross-filter predicates optionally bound to v2.63 grammar specifications and data bindings.
- Brush ranges with explicit fields/channels and target views.
- Focus/highlight state contracts.
- Propagation evidence describing externally applied or rejected linked-view state.
- Immutable, revisioned, SHA-256 hash-chained linked-view snapshots.

## Integrity rules

Every source and target view must already be assigned to the composition. Grammar/data-binding references must belong to the same scene. Link policies cannot be borrowed from another composition. Public bundles require both the scene and composition to be public.

## Core boundary

Core registers and preserves interaction contracts. Query execution, actual dataset filtering, browser event dispatch, brush handling, highlight rendering, selection computation, automatic cross-filter execution, and visual inference remain outside Core.
