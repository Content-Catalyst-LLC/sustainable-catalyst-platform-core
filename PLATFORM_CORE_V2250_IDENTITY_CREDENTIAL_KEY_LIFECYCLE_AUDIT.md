# Platform Core v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle Audit

## Release invariants
- Runtime version: `2.25.0`
- Migration head: `0028`
- Secret values persisted by lifecycle subsystem: **false**
- Automatic secret generation: **false**
- Automatic secret distribution: **false**
- Automatic key rotation: **false**
- Public secret references exposed: **false**
- Public key IDs/fingerprints exposed: **false**
- External public-key signature verification: **deferred**

## Durable objects
1. Credential registry records
2. Credential key versions
3. Credential rotation records
4. Credential lifecycle events
5. Credential-use events

## Governed bindings
The release can track environment/secret-manager references for the Core write API key, webhook signing secret, dossier signing secret, and federation trust secret set. The values themselves remain runtime-managed outside the database.
