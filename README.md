# Sustainable Catalyst Platform Core v2.3.0

**Unified Public API and Developer Portal**

Platform Core v2.3.0 turns the internal registry, Knowledge Graph, Evidence Ledger, and provenance system into a governed external developer platform.

The release adds:

- A stable `/api/v1` public surface
- Reviewed registry, graph, evidence, and ledger access
- Developer applications and approval state
- API plans, scopes, quotas, and maximum page sizes
- One-time plaintext API-key issuance
- SHA-256-only key storage
- Per-minute and daily rate limits
- Request IDs and usage records
- Hashed client network and user-agent identifiers
- Signed webhooks with an outbox and delivery history
- Public OpenAPI documentation
- An interactive API console
- Python and JavaScript SDK downloads
- A Postman collection
- WordPress Developer Portal and plan shortcodes
- Migration `0004`

Existing `/v1` product integrations remain available. The unified `/api/v1` routes are additive and intentionally narrower.

## Architectural principle

> Public access should expose useful, reviewed, machine-readable knowledge without exposing administrative controls, internal credentials, private records, or mutable platform state.

## Public API design

All unified public API responses use one envelope:

```json
{
  "data": {},
  "meta": {
    "api_version": "v1",
    "request_id": "4cd56bf912d74fcf8cbcc3d84f11a2aa",
    "documentation": "/developers"
  }
}
```

Authenticate with either:

```http
Authorization: Bearer scpk_your_key
```

or:

```http
X-SC-Public-Key: scpk_your_key
```

Every public response includes:

```text
X-Request-ID
X-SC-API-Version
X-RateLimit-Limit-Minute
X-RateLimit-Remaining-Minute
X-RateLimit-Limit-Day
X-RateLimit-Remaining-Day
```

Rate-limited responses also include `Retry-After`.

## Public API domains

### Service

```text
GET /api/v1/status
```

Scope: `public:status`

### Universal Entity Registry

```text
GET /api/v1/entities
GET /api/v1/entities/{entity_id}
GET /api/v1/entities/{entity_id}/jsonld
GET /api/v1/predicates
```

Scope: `registry:read`

### Knowledge Graph

```text
GET /api/v1/graph/{entity_id}
GET /api/v1/graph/{entity_id}/neighborhood
GET /api/v1/graph/{entity_id}/recommendations
GET /api/v1/graph/path
```

Scope: `graph:read`

### Evidence Ledger

```text
GET /api/v1/claims
GET /api/v1/claims/{claim_id}
GET /api/v1/evidence-records
GET /api/v1/evidence-records/{evidence_id}
GET /api/v1/evidence/manifests/{claim_id}
```

Scope: `evidence:read`

The public evidence surface returns public claims and verified evidence. Review assignments and nonverified evidence are excluded from public manifests.

### Ledger integrity

```text
GET /api/v1/ledger/verify
GET /api/v1/ledger/entries
```

Scope: `ledger:read`

The public ledger route exposes evidence-domain record types. Developer applications, API credentials, and other administrative records are not exposed.

### Developer identity and usage

```text
GET /api/v1/developer/me
GET /api/v1/developer/usage
```

Scope: `developer:read`

### Webhook subscriptions

```text
GET   /api/v1/developer/webhooks
POST  /api/v1/developer/webhooks
PATCH /api/v1/developer/webhooks/{subscription_id}
GET   /api/v1/developer/webhooks/{subscription_id}/deliveries
```

Scope: `webhooks:manage`

## API plans

Three seed plans are included:

| Plan | Requests/minute | Requests/day | Maximum page size | Public |
|---|---:|---:|---:|---|
| Public Research | 60 | 5,000 | 100 | Yes |
| Standard Integration | 300 | 50,000 | 200 | Yes |
| Sustainable Catalyst Internal | 2,000 | 500,000 | 1,000 | No |

Plans can be changed in the database or extended through later administration interfaces.

## API-key security

Public API keys use the form:

```text
scpk_<prefix>_<random-secret>
```

Platform Core:

- Returns the plaintext key once at issuance
- Stores only its SHA-256 hash
- Stores a prefix and last four characters for identification
- Assigns explicit scopes
- Supports expiration and revocation
- Requires an approved developer application
- Rejects scopes not allowed by the assigned plan
- Sends `Cache-Control: no-store` when returning a new key

A lost plaintext key cannot be recovered. Revoke it and issue a replacement.

## Developer application workflow

Administrative routes remain under the internal Platform Core write key.

### Create an approved application

```bash
curl -X POST "https://YOUR-PLATFORM-CORE.onrender.com/v1/developer/applications" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "name": "Example Public Research Integration",
    "owner_name": "Example Developer",
    "owner_email": "developer@example.org",
    "organization": "Example Organization",
    "website_url": "https://example.org",
    "use_case": "Build a public-interest research integration using reviewed Sustainable Catalyst registry, graph, and evidence records.",
    "status": "approved",
    "plan_id": "free",
    "metadata": {},
    "actor": "platform-administrator"
  }'
```

### Issue a scoped key

```bash
curl -X POST \
  "https://YOUR-PLATFORM-CORE.onrender.com/v1/developer/applications/APPLICATION_ID/credentials" \
  -H "Content-Type: application/json" \
  -H "X-SC-API-Key: YOUR_INTERNAL_WRITE_KEY" \
  -d '{
    "label": "Production integration",
    "scopes": [
      "public:status",
      "registry:read",
      "graph:read",
      "evidence:read",
      "ledger:read",
      "developer:read",
      "webhooks:manage"
    ],
    "created_by": "platform-administrator",
    "metadata": {}
  }'
```

Copy the returned `api_key` immediately.

## Webhooks

Webhook event patterns support:

```text
*
claim.*
evidence.*
claim.created
evidence.reviewed
```

The system emits events for registry, relationship, claim, snapshot, provenance, calculation, evidence, and review operations.

Webhook deliveries include:

```http
X-SC-Webhook-ID: sc:webhook-event:...
X-SC-Webhook-Timestamp: 1783650000
X-SC-Webhook-Signature: v1=<hex-hmac>
```

Verify HMAC-SHA256 over:

```text
{timestamp}.{raw_request_body}
```

using the subscription signing secret.

Production callback URLs:

- Must use HTTPS
- Cannot target localhost
- Cannot target private, loopback, link-local, reserved, or unspecified IP addresses
- Cannot contain embedded credentials

Failed deliveries remain pending for retry.

Dispatch pending webhooks:

```bash
cd backend
.venv/bin/python scripts/dispatch_webhooks.py --limit 100
```

The same operation is available administratively:

```text
POST /v1/developer/webhooks/dispatch
```

## Developer Portal

Open:

```text
https://YOUR-PLATFORM-CORE.onrender.com/developers
```

Included:

- Public API overview
- Scope and quota documentation
- Interactive GET console
- Public OpenAPI JSON
- Python SDK download
- JavaScript SDK download
- Postman collection
- Webhook signing documentation

## Local setup

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
.venv/bin/python scripts/migrate.py
.venv/bin/python scripts/seed_registry.py

.venv/bin/python -m uvicorn app.main:app --reload --port 8090
```

Open:

```text
http://127.0.0.1:8090/developers
http://127.0.0.1:8090/developers/console
http://127.0.0.1:8090/developers/openapi.json
http://127.0.0.1:8090/explorer
http://127.0.0.1:8090/evidence-explorer
http://127.0.0.1:8090/docs
```

## Production environment

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: ./start.sh
PYTHON_VERSION=3.12.11
```

Required:

```text
SC_CORE_ENVIRONMENT=production
SC_CORE_DATABASE_URL=<Render PostgreSQL internal database URL>
SC_CORE_WRITE_API_KEY=<long random internal secret>
SC_CORE_CORS_ORIGINS=https://sustainablecatalyst.com
SC_CORE_PUBLIC_READS=true
SC_CORE_MAX_GRAPH_DEPTH=4
SC_CORE_PAGE_SIZE_MAX=200
SC_CORE_EXPLORER_ENABLED=true
SC_CORE_EVIDENCE_EXPLORER_ENABLED=true
SC_CORE_SNAPSHOT_EXCERPT_MAX=1200

SC_CORE_PUBLIC_API_ENABLED=true
SC_CORE_DEVELOPER_PORTAL_ENABLED=true
SC_CORE_PUBLIC_API_DEFAULT_PLAN=free
SC_CORE_API_LOG_SALT=<long random secret>
SC_CORE_WEBHOOK_SIGNING_SECRET=<different long random secret>
SC_CORE_WEBHOOK_DELIVERY_TIMEOUT=10
```

In production, the public API fails closed when `SC_CORE_API_LOG_SALT` is missing. Webhook subscription creation fails closed when `SC_CORE_WEBHOOK_SIGNING_SECRET` is missing.

## WordPress shortcodes

```text
[sc_platform_core_status]
[sc_platform_core_entity id="sc:product:workbench"]
[sc_platform_core_relationships id="sc:product:research-librarian"]
[sc_knowledge_explorer]

[sc_evidence_ledger_status]
[sc_evidence_manifest claim_id="sc:claim:..."]
[sc_evidence_explorer]

[sc_developer_portal]
[sc_public_api_plans]
```

The WordPress plugin remains a thin public connector. It does not store or issue developer credentials.

## Privacy and operational boundaries

Request usage records include:

- Application and credential IDs
- Request path, method, status, duration, and response size
- Required scope
- Request ID
- SHA-256 hashes of client IP and user-agent values salted with `SC_CORE_API_LOG_SALT`

Raw client IP addresses and raw user-agent strings are not stored.

The in-database rate limiter is suitable for the current single-service Platform Core deployment. A distributed rate-limit backend remains a future requirement if the API is horizontally scaled across multiple database replicas or high-throughput service instances.

## License

MIT
