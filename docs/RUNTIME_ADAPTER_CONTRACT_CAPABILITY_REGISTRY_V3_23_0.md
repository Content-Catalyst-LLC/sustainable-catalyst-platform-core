# Platform Core v3.23.0 — Runtime Adapter Contract & Capability Registry

## Purpose

v3.23.0 turns the v3.22.0 Computational Runtime Object Model into an adapter-facing contract.

Core can now describe *how* a runtime provider participates in the platform without making Core itself responsible for interpreter/compiler execution.

## Required adapter methods

Every native runtime adapter declares:

1. health
2. version
3. capabilities
4. prepare
5. execute
6. cancel
7. inspect
8. collect_results
9. collect_artifacts
10. diagnose

These are contract methods, not direct Python calls into an interpreter.

## Capability Registry

The registry indexes runtime capabilities and operations and supports requirement-to-candidate matching.

Resolution is deliberately `candidate-discovery-only`. Core returns compatible candidates; it does not autonomously choose a scientific method or provider.

## Julia reference adapter

Catalyst Julia Runtime v0.2.0 is registered as the reference adapter in `contract-only` state. It already provides `sc.execution.v1` and `sc.environment.v1`. The next Julia release, v0.3.0, implements this Core adapter contract natively.

## Existing Analytics R compatibility

The release includes a bridge function for the existing `sc.core.analytical-runtime-provider.v1` provider metadata. This prevents the existing Catalyst Analytics R registry from being discarded while the new universal runtime fabric is introduced.

The bridge is transitional. R should later implement `sc.core.runtime-adapter.v1` directly.

## Persistence

No duplicate runtime-provider tables are introduced in this release. Existing analytical-provider persistence remains authoritative for the legacy provider layer. Native universal runtime persistence is deferred until the contract and Julia reference adapter have both stabilized.
