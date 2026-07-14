# Unified Public API

## Base path

```text
/api/v1
```

The public API is additive. Existing `/v1` routes are retained for Sustainable Catalyst products and administrative integrations.

## Authentication

Use either:

```text
Authorization: Bearer scpk_...
```

or:

```text
X-SC-Public-Key: scpk_...
```

## Response envelope

```json
{
  "data": {},
  "meta": {
    "api_version": "v1",
    "request_id": "...",
    "documentation": "/developers"
  }
}
```

## Public scopes

| Scope | Access |
|---|---|
| `public:status` | Service status |
| `registry:read` | Public entities, predicates, and JSON-LD |
| `graph:read` | Reviewed graph traversal, paths, neighborhoods, and recommendations |
| `evidence:read` | Public claims, verified evidence, and filtered manifests |
| `ledger:read` | Public ledger records and whole-chain verification |
| `developer:read` | Credential identity and usage |
| `webhooks:manage` | Application-owned webhook subscriptions and delivery history |

## Public data filtering

The public API excludes:

- Private or internal claims
- Unverified evidence by default
- Evidence review assignments
- Developer application ledger entries
- API credential ledger entries
- Internal administrative records

Ledger verification remains a whole-chain integrity check because filtering entries would invalidate the underlying chain.

## Versioning

The URL path provides the major contract version. Backward-compatible additions may be released within `/api/v1`. A breaking public contract requires `/api/v2`.

Every response also includes:

```text
X-SC-API-Version: 1
```

## Pagination

List routes use `limit` and `offset`. The assigned API plan controls maximum page size.

## Errors

The API uses standard HTTP status codes:

- `401` missing, invalid, revoked, or inactive credential
- `403` missing scope or inactive application/plan
- `404` missing or nonpublic resource
- `422` invalid request
- `429` rate limit or daily quota exceeded
- `503` production security configuration is incomplete

## Request IDs

Clients may supply `X-Request-ID`. Platform Core truncates it to 64 characters. If omitted, Platform Core generates one. The request ID is echoed in the response and retained in usage records.

## v2.5.0 workflow and dossier routes

Scopes:

```text
workflow:read
dossier:read
```

Routes:

```text
GET /api/v1/workflow-definitions
GET /api/v1/workflow-runs/{run_id}
GET /api/v1/dossiers
GET /api/v1/dossiers/{dossier_id}
GET /api/v1/dossiers/{dossier_id}/verify
```

Only public workflow runs and public finalized or superseded dossiers are returned.


## International Law and UN v2.7.1

- `GET /api/v1/international-law/records`
- `GET /api/v1/international-law/records/{record_id}`
- `GET /api/v1/international-law/authority-taxonomy`

These routes use the existing `data:read` scope. They return normalized public legal records; raw provider payloads and internal connector configuration remain private.
