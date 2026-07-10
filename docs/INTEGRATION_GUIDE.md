# Integration Guide

## Choosing an API surface

Use `/v1` when:

- The caller is a trusted Sustainable Catalyst product
- The operation requires the internal write key
- The integration creates claims, evidence, relationships, or snapshots
- The integration manages developer applications or publishes events

Use `/api/v1` when:

- The caller is an external developer or public integration
- The integration needs stable read access
- The caller should have explicit scopes and quotas
- Usage must be attributable to an application and credential
- The integration manages its own webhook subscriptions

## Research Librarian

External research tools can use:

```text
GET /api/v1/entities
GET /api/v1/graph/{entity_id}
GET /api/v1/graph/path
GET /api/v1/claims
GET /api/v1/evidence-records
GET /api/v1/evidence/manifests/{claim_id}
```

Recommended scopes:

```text
registry:read
graph:read
evidence:read
ledger:read
```

## Workbench

Workbench remains an internal writer. It should continue using `/v1` to create:

- Provenance activities
- Calculation traces
- Evidence records
- Graph relationships
- Webhook events when needed

A public calculator client can use `/api/v1` for reviewed metadata and evidence but should not receive the internal write key.

## Decision Studio

Decision Studio remains an internal writer for:

- Claims
- Evidence records
- Review assignments
- Evidence manifests
- Developer-facing webhook events

Public decision-packet viewers can use `/api/v1`.

## Site Intelligence

Site Intelligence remains an internal writer for:

- Source entities
- Source snapshots
- Connector provenance
- Indicator relationships

Public dashboards can consume selected records through `/api/v1`.

## API-key onboarding

1. Create a developer application.
2. Review the use case.
3. Approve or reject it.
4. Assign a plan.
5. Issue a least-privilege key.
6. Deliver the plaintext key once.
7. Ask the developer to verify `/api/v1/status`.
8. Monitor `/api/v1/developer/usage` and internal developer statistics.
9. Revoke and replace keys when compromised or lost.

## Webhook verification

Given:

```text
timestamp = X-SC-Webhook-Timestamp
signature = X-SC-Webhook-Signature
body = exact raw request body
```

Compute:

```text
HMAC_SHA256(subscription_secret, timestamp + "." + body)
```

Compare the hexadecimal digest to the `v1=` signature using a constant-time comparison.

Reject:

- Old timestamps outside the consumer's replay window
- Missing signatures
- Invalid signatures
- Duplicate webhook IDs already processed

## Python SDK

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.entities(entity_type="product"))
print(client.verify_ledger())
```

## JavaScript SDK

```javascript
import { PublicApiClient } from "./index.mjs";

const client = new PublicApiClient(
  "https://YOUR-PLATFORM-CORE.onrender.com",
  "scpk_your_key"
);

console.log(await client.status());
console.log(await client.entities({ entity_type: "product" }));
```

## WordPress

```text
[sc_developer_portal]
[sc_public_api_plans]
```

The WordPress connector links to the backend Developer Portal. It does not store public developer keys or the internal write key.
