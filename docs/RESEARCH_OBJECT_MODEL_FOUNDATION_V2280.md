# Research Object & Model Foundation — v2.28.0

Platform Core v2.28.0 adds a graph-native research object layer without turning Core into a numerical execution engine.

## Canonical object types

- `research-project`
- `model`
- `model-version`
- `variable`
- `parameter`
- `scenario`
- `model-run`
- `result`

Each object is anchored to the existing Universal Entity Registry. Typed extension tables carry research/model semantics while the existing Knowledge Graph supplies relationships and navigation.

## Graph semantics

v2.28.0 deliberately reuses the existing predicate vocabulary rather than creating a parallel graph:

- model `part_of` research project
- model version `version_of` model
- variable/parameter `part_of` model
- scenario `part_of` project
- derived scenario `derived_from` base scenario
- model run `uses` model version and optional scenario
- result `derived_from` model run

## Reproducibility

Model versions carry a deterministic SHA-256 specification hash and can be declared immutable. Variables can carry units, domain constraints, and uncertainty metadata. Parameters support defaults, bounds, priors, and sensitivity flags. Scenario records persist parameter assignments and assumptions.

Model runs may link existing `ProvenanceActivity` and `CalculationTrace` records. Results may reference scientific stored objects introduced in v2.27.0.

## Execution boundary

Platform Core does not execute models. A model or model run can identify `lab`, `workbench`, or `external` as its execution target/executor. Core governs identity, structure, routing intent, graph relationships, provenance linkage, and reproducibility metadata.

No model output is automatically promoted to evidence, claim truth, or decision authority.

## APIs

Internal:

- `GET /v1/research-objects/readiness`
- `POST /v1/research-objects`
- `GET /v1/research-objects`
- `GET /v1/research-objects/{entity_id}`
- `GET /v1/research-objects/projects/{project_entity_id}/bundle`

Public metadata:

- `GET /api/v1/research-objects/readiness`
- `GET /api/v1/research-objects`
- `GET /api/v1/research-objects/{entity_id}`
- `GET /api/v1/research-objects/projects/{project_entity_id}/bundle`

Public endpoints expose only public research objects and never provide an execution surface.
