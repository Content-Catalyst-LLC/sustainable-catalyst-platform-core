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

## Scientific data v2.7.2

Credentials with `data:read` may access:

```text
GET /api/v1/science/records
GET /api/v1/science/records/{record_id}
GET /api/v1/science/record-types
```

The list endpoint supports record type, discipline, source, connector, collection, mission, instrument, target, dataset, query, and observation-date filters. Public endpoints return normalized metadata only; raw provider payloads remain internal.


## Economics and official statistics v2.7.3

Credentials with `data:read` may access:

```text
GET /api/v1/economics/records
GET /api/v1/economics/records/{record_id}
GET /api/v1/economics/record-types
```

The list endpoint supports record type, subject, source, connector, indicator, dataset, geography, frequency, text, and date filters. Public responses expose normalized records only; raw provider payloads, credential configuration, and internal ingestion details remain private.


## Geospatial, time-series, scientific assets, and STAC v2.8.0

Scoped `data:read` routes:

```text
GET /api/v1/fabric/capabilities
GET /api/v1/fabric/features
GET /api/v1/fabric/features.geojson
GET /api/v1/fabric/timeseries
GET /api/v1/fabric/timeseries/{series_id}/points
GET /api/v1/fabric/assets
GET /api/v1/fabric/map-layers
GET /api/v1/stac
GET /api/v1/stac/collections
GET /api/v1/stac/collections/{collection_id}
GET /api/v1/stac/collections/{collection_id}/items
GET /api/v1/stac/search
```

STAC and GeoJSON routes return their standard raw documents rather than the Sustainable Catalyst envelope.
