# Platform Core v3.41.0 — Reproducible Environment Packages

## Objective

v3.41.0 turns execution-environment provenance into portable, governed
environment packages that can be reconstructed and verified by Workspace or
another execution host.

Contract: `sc.core.reproducible-environment-package.v1`

This release builds directly on the v3.24 environment provenance model and the
v3.40 cross-runtime workflow layer.

## First-class objects

- PlatformDescriptor
- RuntimeEnvironmentRequirement
- SystemPackageRequirement
- LanguagePackageRequirement
- EnvironmentVariableDeclaration
- EnvironmentAsset
- EnvironmentBuildInstruction
- ReproducibleEnvironmentPackage
- EnvironmentReproductionRequest
- EnvironmentCompatibilityReport
- EnvironmentReproductionVerification
- ReproducibleEnvironmentPackageBundle

## What an environment package captures

A package can freeze:
- operating system and architecture;
- runtime identities and exact versions;
- runtime adapters;
- system packages;
- language packages;
- lockfiles and manifests;
- environment-variable declarations;
- deterministic build instructions;
- source jobs;
- source workflows;
- provenance and package fingerprints.

The package is a reproducibility recipe and evidence object. It is not a
running environment.

## Secrets

Secret values are never embedded.

A secret environment variable may contain only a `secret_ref`. Its value must
remain null. Workspace or the execution host resolves the secret externally
during reproduction.

This allows an environment package to remain portable and inspectable without
becoming a credential archive.

## Ordered build recipe

Build instructions are explicitly ordered and must have contiguous ordinals.
Instructions may reference known requirements and known build assets only.

The reference R + Julia package uses:

1. install system packages;
2. restore R lockfile;
3. restore Julia manifest;
4. run environment smoke tests.

Platform Core validates that recipe but does not execute it.

## Compatibility preflight

`EnvironmentCompatibilityReport` compares the frozen platform with a proposed
target platform.

The initial contract uses a conservative rule: operating system and
architecture must match for a `compatible` result. A compatibility report is
only a preflight assessment; it is never proof that reproduction succeeded.

## Reproduction verification

A reproduced environment can be checked against:
- runtime versions;
- system package versions;
- language package versions;
- lockfile/manifest hashes;
- environment-variable declarations;
- smoke-test references.

A verification marked `passed` cannot contain a failed recorded check.

## Reference package

The reference package reproduces the environment behind the v3.40 R→Julia
workflow:

`sc-runtime-r@1.0.0`
+
`catalyst-julia-runtime@0.3.0`
+
Ubuntu 24.04 amd64
+
system dependencies
+
R lockfile
+
Julia Manifest
+
locale/timezone declarations
+
external secret reference
+
smoke tests.

The reference verification is a contract proof and does not claim that a live
environment was rebuilt during local package generation.

## Scientific registry bridge

A reproducible environment package can be projected into a v3.38
`ScientificArtifactRef` using the package fingerprint as its content hash. This
lets research outputs point to the exact computational environment package
required for reproduction.

## Product boundaries

Platform Core owns:
- environment package identity;
- frozen requirements;
- build recipes;
- package fingerprints;
- compatibility reports;
- reproduction verification objects;
- provenance and exchange.

Workspace or another execution host owns:
- package-manager execution;
- container/environment construction;
- package downloads;
- secret resolution;
- smoke-test execution;
- worker/runtime startup.

Core does not install packages, build environments, resolve secrets, or certify
reproduction without verification.

## Next mapped build

Platform Core v3.42.0 — Verification & Reproduction Engine.
