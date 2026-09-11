# Visual Reasoning Object Model — v2.29.0

Platform Core v2.29.0 adds a renderer-neutral semantic layer for visual reasoning. It turns visual explanations into governed Core objects without embedding layout engines, chart libraries, renderer selection, or visual styling in Core.

## Canonical object model

A `visual-reasoning-object` is a Universal Entity Registry object with a typed profile that can be attached to a research project and a primary subject entity. It records:

- `visual_kind`: system-map, flow-map, scenario-landscape, model-map, evidence-map, causal-map, spatial-temporal-map, or generic;
- reasoning purpose: explore, compare, explain, diagnose, or communicate;
- semantic state and coordinate-space intent;
- lens, filters, assumptions, project binding, and primary subject binding.

Each visual reasoning object can contain governed child records:

- **elements** — semantic nodes/states/metrics/groups that can bind to Core entities or scientific stored objects;
- **relations** — dependency, causal, flow, contrast, containment, temporal, support, contradiction, and related semantic links;
- **layers** — context, data, model, scenario, evidence, uncertainty, and annotation groupings;
- **annotations** — claims, caveats, assumptions, uncertainty notes, provenance notes, and decisions;
- **snapshots** — immutable SHA-256 hashes of the semantic state for reproducibility and review.

## Research integration

Visual reasoning objects can be `part_of` a v2.28 research project and `about` any existing Core entity. Elements can bind directly to models, scenarios, variables, parameters, model runs, results, evidence entities, facilities, scientific entities, or other governed entities.

Scientific object bytes remain governed by v2.27 storage. Visual elements store only the scientific object identifier when a binary or file-backed scientific artifact is the source.

## Explicit boundaries

v2.29.0 does **not** add:

- a renderer registry;
- chart or map style specifications;
- automatic layout or graph positioning;
- D3, Plotly, Vega, ECharts, Cytoscape, React Flow, MapLibre, deck.gl, or Three.js runtime execution;
- automatic causal inference;
- automatic truth promotion;
- automatic conversion of model results into evidence.

Those boundaries are intentional. v2.30.0 is the planned **Visualization Specification & Renderer Registry** layer.

## API

Internal API:

- `GET /v1/visual-reasoning/readiness`
- `POST /v1/visual-reasoning/objects`
- `GET /v1/visual-reasoning/objects`
- `GET /v1/visual-reasoning/objects/{id}`
- `GET /v1/visual-reasoning/objects/{id}/bundle`
- `POST /v1/visual-reasoning/objects/{id}/elements`
- `POST /v1/visual-reasoning/objects/{id}/relations`
- `POST /v1/visual-reasoning/objects/{id}/layers`
- `POST /v1/visual-reasoning/objects/{id}/annotations`
- `POST /v1/visual-reasoning/objects/{id}/snapshots`

Scoped public metadata API (`data:read`):

- `GET /api/v1/visual-reasoning/readiness`
- `GET /api/v1/visual-reasoning/objects`
- `GET /api/v1/visual-reasoning/objects/{id}`
- `GET /api/v1/visual-reasoning/objects/{id}/bundle`

Public routes return only objects whose parent Universal Entity Registry visibility is `public`.

## Migration

Migration `0032` creates the visual reasoning object profile and child semantic tables. It is additive and leaves all v2.0.0–v2.28.0 data contracts intact.
