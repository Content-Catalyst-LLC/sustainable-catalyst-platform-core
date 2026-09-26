# Platform Core v3.44.0 — Unified Runtime API & Product Integration

## Objective

v3.44.0 consolidates the runtime fabric behind one language-neutral API
contract for Sustainable Catalyst products.

Contract: `sc.core.unified-runtime-api.v1`

The release composes the runtime object model, adapter registry, computational
jobs, data interchange, cross-runtime workflows, reproducible environments,
verification/reproduction, and runtime security layers into one product-facing
contract.

## First-class objects

- `UnifiedRuntimeCatalogEntry`
- `UnifiedRuntimeCatalog`
- `ProductRuntimeIntegrationProfile`
- `UnifiedRuntimeInput`
- `UnifiedRuntimeOutputContract`
- `UnifiedRuntimeRequest`
- `RuntimeResolutionCandidate`
- `UnifiedRuntimeResolution`
- `UnifiedRuntimeInvocation`
- `ProductRuntimeReceipt`
- `UnifiedRuntimeAPIBundle`

## Unified runtime catalog

The catalog exposes governed runtime identity rather than product-specific
runtime assumptions. Each entry binds:

- runtime identity and version;
- runtime adapter;
- language;
- declared capabilities;
- supported operations;
- interchange formats;
- reproducible environment package;
- runtime security policy;
- isolation profile;
- operational availability.

The v3.44 reference catalog contains the currently governed R and Julia
providers:

- `sc-runtime-r@1.0.0`
- `catalyst-julia-runtime@0.3.0`

## Product runtime profiles

v3.44 defines Core-side integration profiles for:

### Workspace

Role: primary runtime orchestrator.

The profile can request execution, statistical analysis, workflows,
interchange, reproduction, verification and inspection. Workspace remains the
preferred execution host and scheduling layer.

### Research Lab

Role: scientific analysis client.

The profile can use R and Julia through the same runtime contract for
statistical analysis, scientific computation, interchange and verification.

### Workbench

Role: engineering and computational prototyping client.

The profile can request numerical/statistical operations while using the same
runtime identities, environment packages and security contracts.

These profiles make the Core API contract-ready for product adapters. This
Core release does not claim that separate product repositories have already
been patched to consume the API.

## Runtime resolution

Resolution has two governed modes.

### Candidate discovery

A product may ask which registered runtimes satisfy a capability and operation.
Core returns compatible candidates but does not choose one.

Example:

`matrix-compute + matrix_multiply`

returns the Julia runtime as a candidate while leaving `bound_runtime_ref`
empty.

### Explicit binding validation

A product or orchestration layer may explicitly bind a runtime. Core validates
that the requested runtime:

- is present in the catalog;
- is allowed for that product;
- advertises the requested capability;
- supports the requested operation;
- is not unavailable.

Only a validated explicit binding can become an invocation envelope.

## Unified invocation envelope

An invocation freezes the identity of the execution request:

product request
→ validated resolution
→ product runtime profile
→ catalog entry
→ runtime + adapter
→ computational job
→ reproducible environment package
→ security policy
→ security decision
→ execution host
→ input/output contracts.

Core constructs and fingerprints the envelope. Core does not dispatch it.

## Security integration

v3.44 makes the v3.43 security decision a required invocation binding. A
unified invocation therefore cannot be constructed without a
`security_decision_ref`.

The runtime catalog also carries the governing security-policy and isolation
profile references for each provider.

Actual enforcement remains the responsibility of Workspace or the runtime
execution host.

## Product completion receipts

Execution hosts/products can return a `ProductRuntimeReceipt` that binds:

- invocation fingerprint;
- computational job;
- runtime;
- execution host;
- produced artifacts;
- produced results;
- isolation attestation;
- optional reproduction verification;
- failure identity when execution fails.

This gives products one common return contract instead of bespoke runtime
result plumbing.

## Reference integration proof

The reference bundle models a Research Lab regression request:

Research Lab
→ Unified Runtime API
→ explicit `sc-runtime-r@1.0.0` binding
→ `adapter:sc-runtime-r`
→ v3.41 environment package
→ v3.43 security decision
→ Workspace execution host
→ completed product receipt
→ statistical result + scientific artifact.

The reference is a contract proof. It does not claim that Research Lab or
Workbench product-side adapters were modified by this Core-only package.

## Scientific registry bridge

The complete unified-runtime API bundle can be projected into the v3.38
Scientific Result & Artifact Registry using its deterministic bundle
fingerprint as the content hash.

## Product boundaries

Platform Core owns:

- the unified runtime catalog;
- product runtime integration profiles;
- capability/operation resolution;
- explicit runtime-binding validation;
- invocation envelopes;
- runtime/security/environment identity;
- product completion receipt contracts;
- provenance and scientific-registry exchange.

Workspace or another execution host owns:

- scheduling;
- queueing;
- dispatch;
- worker allocation;
- runtime execution;
- retry/cancellation mechanics;
- container/sandbox enforcement.

Products retain their domain-specific business logic and user interfaces.

Core does not autonomously select a runtime, dispatch execution, bypass runtime
security, replace product business logic, or certify scientific validity.

## Persistence

No database migration is introduced.

## Next mapped build

Platform Core v3.45.0 — Runtime Fabric Production Certification.
