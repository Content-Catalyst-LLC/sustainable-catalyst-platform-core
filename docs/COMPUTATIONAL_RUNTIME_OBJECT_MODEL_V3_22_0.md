# Platform Core v3.22.0 — Computational Runtime Object Model

## Purpose

This release introduces the canonical, language-neutral object contract used by Platform Core to describe computational runtimes without absorbing runtime-specific execution behavior into Core.

The object model defines eight first-class contract types:

- Runtime
- Runtime Environment
- Runtime Capability
- Runtime Dependency
- Execution Request
- Execution Run
- Execution Result
- Runtime Artifact

## Architectural boundary

Platform Core owns identity, contracts, lifecycle vocabulary, artifact references, environment references, provenance and reproducibility bindings.

Runtime providers own interpreter/compiler invocation, package-manager behavior, runtime-specific serialization, process lifecycle details and runtime-specific diagnostics.

This release does not make Core an arbitrary-code execution engine and does not autonomously select scientific methods.

## Julia reference runtime

Catalyst Julia Runtime v0.2.0 is the first reference provider. Its existing `sc.execution.v1` and `sc.environment.v1` contracts map cleanly into the new Core object model.

The next Julia build can therefore implement the Core adapter contract without redesigning the v0.1/v0.2 service.

## Deterministic fingerprints

Every normalized object can be serialized using canonical JSON and SHA-256 fingerprinted. This allows later releases to bind jobs, artifacts, reproduction packages and cross-runtime workflows to stable object identities.

## API

- `GET /api/v1/computational-runtime-objects/contract`
- `GET /public/v1/computational-runtime-objects/contract`
- `POST /api/v1/computational-runtime-objects/validate`
- `POST /api/v1/computational-runtime-objects/fingerprint`

## Persistence

v3.22.0 intentionally defines the contract before introducing new persistence tables. Existing analytical provider/result records remain unchanged. Persistent runtime/job/artifact registries arrive in later Runtime Fabric releases, avoiding a second migration when the v3.22 contract stabilizes.
