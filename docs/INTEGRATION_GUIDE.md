# Integration Guide

## Research Librarian

Use:

```text
GET /v1/graph/{entity_id}/neighborhood
GET /v1/graph/{entity_id}/recommendations
GET /v1/graph/path
```

These endpoints support graph-backed source cards, related tools, research routes, and action recommendations.

## Workbench

Recommended relationships:

```text
tool --implements--> model
tool --requires--> dataset
tool --applies_to--> concept
article --uses--> tool
```

## Decision Studio

Use paths and neighborhoods to trace claims to sources, import Workbench tools by stable ID, and preserve relationship review state.

## Site Intelligence

Recommended relationships:

```text
indicator --measured_by--> dataset
dataset --has_source--> source
dashboard --uses--> indicator
connector --uses--> source
```

## WordPress

```text
[sc_platform_core_status]
[sc_platform_core_entity id="sc:product:workbench"]
[sc_platform_core_relationships id="sc:product:research-librarian"]
[sc_knowledge_explorer]
```
