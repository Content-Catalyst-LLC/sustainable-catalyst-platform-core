# Architecture

## Purpose

Platform Core supplies shared identifiers and machine-readable relationships across Sustainable Catalyst.

## Layers

### 1. Registry layer

Stores stable entities, aliases, lifecycle state, visibility, canonical URLs, schema versions, and extensible metadata.

### 2. Relationship layer

Stores typed subject-predicate-object records with confidence, review status, and provenance.

### 3. Foundation records

Provides initial schemas for evidence and validation events. Full workflow logic is reserved for later releases.

### 4. Integration layer

Exposes a versioned FastAPI interface, Python client, WordPress plugin, import adapters, and OpenAPI documentation.

## Entity identifiers

Canonical IDs use:

```text
sc:<entity-type>:<slug>
```

Examples:

```text
sc:article:planetary-boundaries
sc:concept:freshwater-change
sc:indicator:sdg-6-1-1
sc:dataset:world-bank-poverty
sc:source:un-data
sc:tool:emissions-calculator
sc:country:kenya
sc:treaty:paris-agreement
sc:product:workbench
```

The entity type and slug are lowercase and hyphenated. Existing external identifiers are stored as aliases rather than replacing the canonical Sustainable Catalyst ID.

## Relationship vocabulary

The service accepts an extensible predicate string. Recommended initial predicates include:

```text
about
applies_to
broader_than
contradicts
derived_from
has_source
implements
measured_by
measures
narrower_than
part_of
related_to
requires
supports
supersedes
uses
validated_by
```

## Storage

- SQLite is the default for local development and tests.
- PostgreSQL is recommended for Render production.
- The data model uses SQLAlchemy and cross-database migrations.
- Graph traversal is implemented over the relationship table for the v2 foundation.
- A dedicated graph database can be added later behind the service layer without changing public IDs.

## Security

- Reads are public only when `SC_CORE_PUBLIC_READS=true`.
- Writes require `X-SC-API-Key`.
- Production writes are disabled if a key is missing.
- CORS is restricted through `SC_CORE_CORS_ORIGINS`.
- No secret is included in repository files.

## Service boundaries

Platform Core does not execute Workbench calculations, generate Decision Studio briefs, crawl the full website, or replace each product's own domain logic. It gives those products a common identity and relationship system.
