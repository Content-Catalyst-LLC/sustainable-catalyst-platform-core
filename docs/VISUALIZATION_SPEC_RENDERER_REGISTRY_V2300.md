# Platform Core v2.30.0 — Visualization Specification & Renderer Registry

## Purpose
v2.30.0 turns renderer intent into governed metadata without making Platform Core a rendering engine. It sits directly above the v2.29 renderer-neutral Visual Reasoning Object Model.

## First-class records
- `VisualizationSpecificationRecord`: immutable revisioned rendering intent bound to a v2.29 visual reasoning object.
- `RendererDefinitionRecord`: renderer-family contract metadata and execution boundary.
- `RendererVersionRecord`: versioned renderer-contract metadata. Seeded `contract-v1` values are contract versions, not installed package-version claims.
- `RendererCompatibilityRuleRecord`: governed visual-kind/spec-kind compatibility and priority.
- `RendererResolutionRecord`: auditable compatibility-resolution decision with `execution_performed=false`.

## Specification contract
A specification can govern encoding, interaction intent, accessibility requirements, layout constraints, export intent, preferred renderer, and renderer policy. The canonical specification state is SHA-256 hashed. Existing revisions are not mutated through the API; a changed specification is a new revision.

## Seeded renderer-family contracts
Core seeds provider-neutral contract records for D3, Vega-Lite, Plotly, and MapLibre. These records express compatibility metadata only. They explicitly set `executable_by_core=false` and `installed_runtime_asserted=false`.

## Resolution semantics
Resolution matches a visualization specification's `spec_kind` and the bound visual reasoning object's `visual_kind` against enabled compatibility rules. A preferred/requested renderer is selected only if compatible. Otherwise registry priority is deterministic. Resolution records persist the rationale and never execute renderer code.

## Non-goals
Platform Core does not:
- import or execute renderer libraries;
- calculate node/edge or chart layout;
- produce SVG, PNG, canvas, WebGL, HTML, or other visual output;
- decide that a visual claim is true because it rendered successfully;
- provision external rendering infrastructure.

## API
Internal routes are under `/v1/visualization`; public-safe metadata routes are under `/api/v1/visualization`.

Key internal routes:
- `GET /v1/visualization/readiness`
- `POST /v1/visualization/specifications`
- `GET /v1/visualization/specifications`
- `GET /v1/visualization/specifications/{id}`
- `POST /v1/visualization/specifications/{id}/resolve`
- `GET /v1/visualization/renderers`
- `POST /v1/visualization/renderers`
- `GET /v1/visualization/renderers/{renderer_key}`
- `POST /v1/visualization/renderers/{renderer_key}/versions`
- `POST /v1/visualization/renderers/{renderer_key}/compatibility-rules`
- `GET /v1/visualization/specifications/{id}/resolutions`

## Next layer
v2.31.0 is reserved for System Maps built on v2.29 semantic visual objects plus v2.30 governed visualization specifications and renderer contracts.
