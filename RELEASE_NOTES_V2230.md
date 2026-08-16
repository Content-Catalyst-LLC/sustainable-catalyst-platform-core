# Platform Core v2.23.0 — Federated Core & Trusted Node Exchange

v2.23.0 adds governed synchronization between trusted Sustainable Catalyst Core nodes without introducing database mirroring or authority transfer.

## Added
- Trusted remote-node registry and explicit trust relationships.
- Pairwise HMAC-SHA256 manifest authentication using runtime-only environment secrets.
- Pull-based, reference-first exchange manifests with canonical URIs and SHA-256 content hashes.
- Conflict-safe inbound intake that creates remote references rather than overwriting local canonical subjects.
- Signature mismatch rejection, private-record scope controls, public aggregate federation status, SDK helpers, WordPress status, and optional certification gating.
- Additive migration `0026`.

## Hard boundaries
- Trust secrets are not persisted.
- Embedded snapshots/payloads are disabled in federation manifests.
- Automatic truth promotion, ownership transfer, cross-node delivery, governance replication, and local subject overwrite are disabled.
- Federation does not create a new evidence-authority layer.
