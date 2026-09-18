# Platform Core v2.71.0 — Cross-Product Visual Runtime Integration

v2.71.0 moves the v2.70 Unified Visual Reasoning Engine from internal convergence to shared platform consumption. Library, Lab, Workbench, Decision Studio, Site Intelligence, Workspace, and Research Librarian can bind the same Core visual objects, contexts, capabilities, views, and handoff contracts without inventing product-specific visual semantics.

## Added
- Product visual-runtime integration registry.
- Canonical object and research-context bindings.
- Shared visual capability contracts for graph, timeline, map, plot, model, forecast, evidence, decision, notebook, document, and linked-view surfaces.
- Cross-product view bindings and external handoff routes.
- Synchronization evidence records without Core-side state mutation.
- Immutable hash-chained integration snapshots.
- Unified public bundle contract `sc.visual-runtime.cross-product-integration.v1`.

## Boundaries
Platform Core records contracts, routes, references, provenance, and synchronization evidence. It does not render, compute, mutate specialist-product state, execute handoffs, synchronize products automatically, infer conclusions visually, or promote truth automatically.

## Database
Migration `0075` is additive and requires the v2.70 Unified Visual Reasoning Engine schema as its production predecessor.
