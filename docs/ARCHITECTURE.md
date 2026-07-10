# Architecture

## Platform Core layers

### Universal Entity Registry

Stable IDs, aliases, lifecycle state, visibility, canonical URLs, and extensible metadata.

### Governed Knowledge Graph

Controlled predicates, type constraints, relationship reviews, bounded traversal, paths, neighborhoods, recommendations, and JSON-LD.

### Evidence Ledger

Claims, immutable source snapshots, evidence records, calculation traces, review assignments, append-only decisions, manifests, and tamper-evident ledger history.

### Unified Public API

The `/api/v1` layer provides a curated external contract over selected Platform Core read capabilities.

Internal product integrations retain `/v1`. External developers receive:

- Stable versioned paths
- Consistent response envelopes
- Request IDs
- Explicit scopes
- Quotas and maximum page sizes
- Public-record filtering
- Usage visibility
- Webhook management

### Developer control plane

Administrative `/v1/developer` routes manage:

- API plans
- Developer applications
- Approval state
- Credentials
- Revocation
- Usage
- Event publication
- Webhook dispatch
- Platform statistics

These routes require the internal Platform Core write key.

### Credential model

A public API credential stores:

- Application ID
- Human-readable label
- Key prefix
- Last four characters
- SHA-256 key hash
- Scopes
- Status
- Expiration
- Last-use time
- Issuer
- Revocation time

Plaintext keys are never stored.

### Quota model

Rate limits are enforced from request-log records in PostgreSQL or SQLite:

- Rolling one-minute request count
- Calendar-day request count
- Plan-specific maximum page size

This is appropriate for the current single-service deployment. A horizontally scaled high-throughput deployment should add Redis or another distributed counter backend.

### Request privacy

Platform Core does not store raw public API client IP addresses or user-agent strings.

It stores:

```text
SHA256(api_log_salt + ":" + client_value)
```

The salt must be production-specific and secret.

### Webhook model

Webhook events use an outbox:

1. Domain operation creates or updates a Platform Core record.
2. A webhook event is inserted in the same database transaction.
3. The dispatcher resolves matching subscriptions.
4. A canonical JSON body is generated.
5. The body is signed with HMAC-SHA256.
6. Delivery status and response information are recorded.
7. Failed event deliveries remain pending for retry.

The subscription secret is deterministically derived with HMAC-SHA256 from a production master signing secret and the subscription ID.

### Public-data boundary

The public API excludes:

- Administrative developer records
- Credential hashes and secrets
- Private or internal claims
- Nonverified evidence
- Review assignments
- Internal evidence-manifest records
- Unsupported ledger record types
- Mutable registry and evidence writes

## Middleware

`PublicApiMiddleware` runs only for `/api/v1` paths and performs:

1. API-enabled check
2. Production salt check
3. Key extraction
4. SHA-256 key lookup
5. Application, plan, key, and expiration validation
6. Minute and daily quota checks
7. Request-context creation
8. Response quota headers
9. Salted request logging
10. Credential last-use update

Endpoint dependencies enforce the required scope.

## Backward compatibility

The release does not remove or rename the internal `/v1` interfaces introduced in v2.0–v2.2. Existing Sustainable Catalyst product integrations continue to work.
