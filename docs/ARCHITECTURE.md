# Architecture

## Platform Core layers

### Universal Entity Registry

Stable IDs, entity aliases, lifecycle state, visibility, canonical URLs, and metadata.

### Governed Knowledge Graph

Controlled predicates, type constraints, reviewed relationships, traversal, paths, neighborhoods, recommendations, and JSON-LD.

### Evidence Ledger

Claims, source snapshots, evidence records, calculation traces, reviews, assignments, and manifests.

### Provenance layer

Activities identify the agent, software, parameters, environment, timing, and status of a process. Provenance links connect activities to claims, evidence, snapshots, traces, entities, and graph relationships.

### Tamper-evident audit layer

Ledger entries form an ordered hash chain. Each entry binds:

```text
record identity
action
actor
payload hash
previous entry hash
timestamp
```

The chain detects changed payloads, changed entry metadata, missing predecessors, and reordered history.

## Transaction model

A domain record and its corresponding ledger entry are inserted in the same database transaction. If either insertion fails, neither is committed.

## Source-content model

Platform Core stores:

- Content hash
- Length
- Configurable excerpt
- Storage and archive references

It does not require the full source body to remain in the relational database. A later object-storage adapter can preserve full snapshots without changing snapshot IDs.

## Manifest model

Evidence manifests are generated from current linked records and include the relevant ledger history. Their canonical contents are hashed on export.

## Immutability model

Source snapshots, calculation traces, provenance links, reviews, and ledger entries have no update or delete API. Ledger entries also reject ORM updates and deletes.

Claims remain revision-capable because claim language and lifecycle can change; each change creates a new ledger entry.

## Security

- Writes require `X-SC-API-Key`.
- Production writes fail closed without a configured key.
- Public-read settings apply to ledger routes.
- Source content is not returned after snapshot capture.
- WordPress never receives the backend write key.
