# Platform Core v3.22.0 — Computational Runtime Object Model

## Added
- `sc.core.computational-runtime-object.v1`
- Canonical Runtime, Environment, Capability, Dependency, Execution Request, Execution Run, Execution Result and Artifact objects.
- Deterministic canonical-JSON SHA-256 fingerprints.
- Explicit resource-budget and execution-policy objects.
- Julia v0.2.0 environment-lock compatibility.
- Contract validation and fingerprint API endpoints.
- Public contract discovery endpoint.
- Additive release tests and backend validation.

## Boundaries
- Core does not execute arbitrary source code.
- Core does not install language packages.
- Core does not autonomously choose a scientific method.
- Core does not certify scientific validity or determine truth.

## Versioning note
Platform Core v3.21.0 is already an immutable release for Uncertainty & Probabilistic Evidence Integration. The Runtime Object Model therefore begins at v3.22.0.
