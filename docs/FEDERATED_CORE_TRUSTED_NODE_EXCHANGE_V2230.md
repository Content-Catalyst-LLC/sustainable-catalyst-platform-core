# Federated Core & Trusted Node Exchange — v2.23.0

Federation is a governed reference-exchange layer between Core installations. It is intentionally not database replication.

A remote node must first be registered and placed inside an explicit trust relationship. Trust scope can limit subject types and whether private/restricted references are permitted. Snapshot exchange remains disabled.

Manifests carry canonical subject references, SHA-256 hashes, visibility, and provenance metadata. Pairwise trust secrets are supplied by `SC_CORE_FEDERATION_TRUST_SECRETS_JSON` at runtime and are never written to the database. HMAC-SHA256 authenticates the canonical manifest body.

Inbound manifests must target the local node, satisfy trust scope, preserve `reference_first=true`, and explicitly keep automatic truth promotion and ownership transfer false. Acceptance creates `FederationRemoteReference` records only. It does not mutate a canonical local claim, evidence record, source snapshot, governance policy, or ownership record.

Public status is aggregate-only. Node identities, endpoints, trust details, manifests, signatures, and remote-reference contents stay internal.
