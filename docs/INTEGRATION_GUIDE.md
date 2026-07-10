# Integration Guide

## Research Librarian

Use Platform Core to:

- Resolve a page, concept, tool, source, or article to one canonical entity
- Retrieve related products and research paths
- Return graph-backed source and route cards
- Store external page IDs as aliases

Suggested relationship queries:

```text
article --about--> concept
concept --related_to--> concept
article --has_source--> source
article --uses--> tool
```

## Workbench

Use Platform Core to:

- Register calculators as `tool` entities
- Connect tools to articles, equations, datasets, and concepts
- Create evidence foundation records for calculation outputs
- Publish validation events for calculator tests

Suggested relationships:

```text
tool --implements--> model
tool --requires--> dataset
tool --applies_to--> concept
article --uses--> tool
```

## Decision Studio

Use Platform Core to:

- Resolve imported artifacts to canonical entities
- Preserve source and tool IDs in decision packets
- Store decision-support evidence foundations
- Link claims to supporting or contradicting sources

Suggested relationships:

```text
claim --supports/contradicts--> claim
claim --has_source--> source
decision-packet --uses--> evidence
decision-packet --uses--> tool
```

## Site Intelligence

Use Platform Core to:

- Register connectors, datasets, indicators, dashboards, jurisdictions, and sources
- Import existing source registry manifests
- Link indicators to datasets and sources
- Publish freshness and schema validation events

Suggested relationships:

```text
indicator --measured_by--> dataset
dataset --has_source--> source
dashboard --uses--> indicator
connector --uses--> source
```

## WordPress

The bundled plugin supports:

- Backend URL and optional read key configuration
- Health and statistics display
- Entity lookup shortcode
- Status shortcode

Shortcodes:

```text
[sc_platform_core_status]
[sc_platform_core_entity id="sc:product:workbench"]
```
