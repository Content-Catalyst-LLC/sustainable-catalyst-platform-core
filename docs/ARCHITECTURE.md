# Architecture

Platform Core v2.1.0 supplies shared identifiers, controlled relationship meaning, graph intelligence, and machine-readable interoperability across Sustainable Catalyst.

## Layers

### Universal Entity Registry

Stable entities, aliases, lifecycle state, visibility, canonical URLs, schema versions, and extensible metadata.

### Predicate Registry

Controlled vocabulary with:

- Label and description
- Optional inverse
- Symmetric and transitive flags
- Allowed subject types
- Allowed object types
- Lifecycle and visibility

### Relationship Engine

- Inbound, outbound, and bidirectional traversal
- Shortest paths
- Confidence and review-status filtering
- Direct neighborhoods
- Related-entity recommendations
- Append-only review history

### Interoperability

- FastAPI/OpenAPI
- JSON-LD
- Python client
- WordPress connector
- Site Intelligence manifest adapter
- Public Knowledge Explorer

## Storage strategy

PostgreSQL remains the recommended production store. Graph behavior sits behind service interfaces, so a dedicated graph database can be added later without changing Sustainable Catalyst entity IDs or public APIs.

## Security

Writes require `X-SC-API-Key`. The Knowledge Explorer uses public read endpoints only. The WordPress connector never exposes the write key in frontend code.
