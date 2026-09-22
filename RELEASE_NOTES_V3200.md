# Platform Core v3.2.0 — Analytical Result & Provenance Integration

Platform Core v3.2.0 promotes externally computed analytical outputs into first-class, provenance-aware Core research objects. It consumes the `sc.core.analytical-runtime-provider.v1` result contract established in v3.1.0 and implemented by Catalyst Analytics R v2.1.0 / Workspace v3.5.0.

## Delivered
- Migration `0104`.
- First-class analytical result objects with stable fingerprints and provenance hashes.
- Workspace ingestion receipts and idempotent replay protection.
- First-class estimate and uncertainty objects.
- Explicit analytical lineage edges covering inputs, outputs, provider, environment, Workspace receipt, execution, diagnostics, artifacts, estimates, uncertainty, and reproduction references.
- Immutable analytical result snapshots with hash-chain linkage.
- Backward-compatible population of the v3.1 execution-result registry.
- Catalyst Analytics R provider registry promoted to `2.1.0`, with Workspace adapter release `3.5.0`.
- Public-safe result bundle and lineage APIs plus SDK and WordPress status integration.

## Boundary
Core does not execute R/Python/Julia analysis, infer statistical significance, certify scientific validity, rank results, determine truth, or autonomously select a provider. Workspace and specialist runtimes execute computation; Core records declared results and provenance for subsequent research reasoning and review.
