# Platform Core v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle

v2.25.0 adds governed credential/key lifecycle metadata without turning Platform Core into a secret store.

## Added
- migration `0028`;
- credential registry metadata and external secret references;
- key identifiers, versions, algorithms, SHA-256 fingerprints, activation and expiry;
- operator-triggered overlap-aware rotations;
- revocation and compromise response lineage;
- service-consumer and allowed-operation policy metadata;
- credential lifecycle and credential-use audit events;
- Core bootstrap metadata for write API, webhook signing, dossier signing and federation trust bindings;
- public-safe aggregate credential health;
- optional certification gating;
- Python/JavaScript SDK and WordPress status helpers.

## Security boundary
Secret values, private keys, bearer tokens and credentials are not persisted. Rotation does not generate, distribute, or automatically activate secrets. External public-key verification remains deferred.
