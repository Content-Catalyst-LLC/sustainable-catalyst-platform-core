# Platform Core v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle

## Purpose

v2.25.0 governs credential and key **metadata** without turning Core into a secret vault. Durable records describe ownership, purpose, external secret location, allowed consumers/operations, key identifiers, versions, fingerprints, expiry, rotation overlap, revocation, compromise response and usage evidence.

## Secret boundary

Core does not persist credential values, private keys, bearer tokens or secret material. A credential registration stores only a locator such as `env:SC_CORE_WEBHOOK_SIGNING_SECRET`, `vault:path/to/item`, `kms:key-id`, `secret-manager:item`, or `external:provider-reference`.

Pydantic write contracts reject undeclared secret-value fields. Durable metadata/context sanitization strips credential-like keys before persistence. `CredentialKeyVersion.secret_value_persisted` is hard-coded false by service logic and is surfaced as a release invariant.

## Governed lifecycle

1. Register credential metadata and service-use policy.
2. Register a staged key version with identifier, algorithm, optional SHA-256 fingerprint and expiry.
3. An operator explicitly activates/rotates to that version.
4. If another version is active, the prior version enters a bounded overlap/retiring state.
5. An operator completes the rotation and the prior version becomes retired.
6. Revocation and compromise are explicit, timestamped lifecycle events and degrade readiness until remediated.
7. Credential-use audit events store service/operation/success/context metadata only.

## Core bootstrap bindings

The operator-only bootstrap route can register secret-free metadata for:
- Core write API authentication;
- outbound webhook signing;
- dossier signing;
- federation shared-secret bindings.

It never reads or copies the secret values into the database.

## Public boundary

`GET /api/v1/credentials/status` exposes only aggregate state and counts. Secret references, key identifiers and fingerprints are intentionally excluded.

## Non-goals

v2.25.0 does not generate, distribute or automatically rotate secrets. It does not implement public-key verification or qualified electronic signatures. Those remain separate later trust capabilities.
