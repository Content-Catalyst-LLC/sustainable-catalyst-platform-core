# Platform Core v2.30.0 — Visualization Specification & Renderer Registry

Released: 2026-09-11

## What changed
Platform Core now governs immutable visualization specifications and a renderer-contract registry on top of v2.29 visual reasoning semantics. Migration `0033` adds specification records, renderer definitions, renderer contract versions, compatibility rules, and non-executing renderer-resolution records. Authorized write APIs can register additional renderer contracts, contract versions, and compatibility rules without granting Core renderer execution.

## Renderer boundaries
The seeded D3, Vega-Lite, Plotly, and MapLibre entries are compatibility contracts only. Core does not assert those libraries are installed, does not execute them, does not calculate layout, and does not produce rendered output. Every resolution record stores `execution_performed=false`.

## Reproducibility
Visualization specification revisions are immutable through the API and receive canonical SHA-256 state hashes. Changes create a new revision rather than rewriting a prior specification.

## Integration
v2.30.0 updates internal/public APIs, registry statistics, capability metadata, Python/JavaScript public SDKs, the WordPress connector, schemas, release validation, and production deployment instructions. The v2.29.0.1 WordPress backend URL diagnostics remain included.

## Migration
Database migration head: `0033`.
