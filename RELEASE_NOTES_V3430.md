# Platform Core v3.43.0 — Runtime Security, Isolation & Governance

## Objective

v3.43.0 adds a governed security contract around runtime execution,
cross-runtime workflows, reproducible environments and reproduction attempts.

Contract: `sc.core.runtime-security-governance.v1`

The release defines what runtime activity is permitted, what requires explicit
human approval, what must be denied, and how an execution host proves that the
declared isolation policy was actually enforced.

## First-class objects

- RuntimeIsolationProfile
- RuntimeSecurityPolicy
- RuntimeSecurityRequest
- GovernanceApproval
- RuntimeSecurityViolation
- RuntimeSecurityDecision
- IsolationAttestation
- RuntimeSecurityEvent
- RuntimeGovernanceRecord
- RuntimeSecurityGovernanceBundle

## Policy surface

A security policy can govern:
- runtime and adapter allowlists;
- operation allowlists;
- network access;
- filesystem writes;
- package installation;
- secret references;
- shell access;
- arbitrary-code execution;
- artifact egress;
- resource-budget references;
- syscall-policy references;
- mandatory-access-control references.

The policy is content-fingerprinted and versioned.

## Isolation profiles

Isolation profiles describe the controls expected from the execution layer:
- process/container/sandbox/microVM/WASM/remote-worker mechanism;
- network mode;
- filesystem mode;
- package-install mode;
- process/user namespace isolation;
- privilege-escalation policy;
- host-filesystem exposure;
- shell/arbitrary-code policy;
- artifact-egress policy.

Platform Core records the contract. Workspace or the runtime execution host
enforces operating-system/container controls.

## Deterministic security evaluation

`evaluate_security_request()` compares an explicit runtime request with an
explicit policy.

Possible outcomes:
- allow;
- deny;
- requires-approval.

Denied requests preserve typed violations and requested/policy values.

The evaluator does not silently broaden permissions.

## Human approval

Some capabilities may be permitted only with an explicit `GovernanceApproval`.

The reference policy requires approval for `secret-access`.

An approval:
- binds one exact security request;
- names the approved capabilities;
- names the approver;
- has an explicit active/revoked/expired state.

Core will not convert `requires-approval` to `allow` without a matching active
approval object.

## Secrets

Policies govern only secret references. Secret values remain outside Platform
Core and outside reproducible environment packages.

Core does not resolve or store runtime secret values.

## Isolation attestation

A permitted request can be accompanied by an `IsolationAttestation` from the
execution host.

A passed attestation requires explicit enforcement checks, such as:
- network disabled;
- filesystem scoped;
- package install disabled;
- privilege escalation disabled;
- shell disabled;
- arbitrary code disabled.

A passed attestation cannot contain a failed enforcement check.

## Reference governance bundle

The reference bundle demonstrates three paths.

1. R regression:
   - allowed;
   - workspace-only writes;
   - no network;
   - no package installation;
   - research-artifact egress;
   - passed container-isolation attestation.

2. R regression requesting an approved secret reference:
   - secret is on the policy allowlist;
   - `secret-access` requires human approval;
   - an explicit active approval is attached;
   - request becomes allowed.

3. Julia matrix operation requesting arbitrary-code execution:
   - runtime/adapter/operation are otherwise allowed;
   - arbitrary code is disabled by the isolation profile;
   - request is denied;
   - violation and security event are preserved.

## Reproduction integration

v3.43 can bind governance records to v3.42 reproduction packages and v3.40
cross-runtime workflows. This lets later reproduction evidence include not only
which environment and runtime were used, but also the exact security policy
under which execution occurred.

## Product boundaries

Platform Core owns:
- security-policy identity;
- request/decision contracts;
- deterministic policy evaluation;
- approval bindings;
- violation objects;
- isolation-attestation contracts;
- security-event provenance;
- governance packages and exchange.

Workspace / execution hosts own:
- sandbox/container creation;
- kernel controls;
- namespace configuration;
- network enforcement;
- filesystem enforcement;
- package-manager enforcement;
- secret injection;
- worker termination.

Core does not launch sandboxes, apply kernel controls, resolve secret values,
install packages, fabricate approvals, or certify isolation without
attestation.

## Next mapped build

Platform Core v3.44.0 — Unified Runtime API & Product Integration.
