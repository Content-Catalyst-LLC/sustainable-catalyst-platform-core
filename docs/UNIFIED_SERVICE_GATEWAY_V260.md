# Sustainable Catalyst Core v2.6.0

## Unified Service Gateway and Integration Foundation

Platform Core is the single public and internal API entry point. Domain products remain independently deployable services behind Core.

```text
WordPress, public applications, and developers
                     ↓
        Sustainable Catalyst Core v2.6.0
                     ↓
 Site Intelligence | Workbench | Decision Studio
 Research Librarian | Catalyst Finance | Narrative Risk
```

## Responsibilities

Core v2.6.0 provides:

- Environment-backed service discovery
- Sanitized service catalog
- Aggregated health checks
- Correlation IDs across Core and downstream services
- Server-side service tokens
- Request and response size limits
- Method allowlists
- Bounded request and health-check timeouts
- Per-service circuit breakers
- Transparent internal proxying
- Read-only unified public routes
- Shared response metadata for JSON routes

Domain services retain their own calculations, connectors, retrieval logic, exports, and product-specific workflows.

## Canonical routes

Internal server-to-server routes use the Core write key:

```text
GET  /v1/gateway/services
GET  /v1/gateway/health
*    /v1/gateway/{service_id}/{downstream_path}
```

Public developer routes use a Platform Core public API credential with `gateway:read`:

```text
GET /api/v1/gateway/services
GET /api/v1/gateway/health
GET /api/v1/site-intelligence/{path}
GET /api/v1/workbench/{path}
GET /api/v1/decision-studio/{path}
GET /api/v1/research-librarian/{path}
GET /api/v1/finance/{path}
GET /api/v1/narrative-risk/{path}
```

Public write/invocation routes are intentionally deferred. WordPress server-side integrations can use the internal gateway with the Core write key while the developer credential model is expanded.

## Security boundary

- Product base URLs and service tokens never appear in public catalog responses.
- Authorization and cookie headers are not forwarded downstream.
- Only a conservative request-header allowlist is forwarded.
- Redirects are not followed automatically.
- `.` and `..` path segments are rejected.
- Request and response sizes are bounded.
- Production errors can be masked by default.
- Downstream services should accept traffic only from Core where infrastructure permits.

## Environment variables

See `deployment/platform-core-v260.env.example`.

## Operational boundaries

- Circuit state is process-local in v2.6.0. A later distributed gateway release can move shared circuit and quota state to Redis or PostgreSQL when Core runs multiple replicas.
- Core does not retry proxied write requests. This avoids accidentally repeating non-idempotent downstream actions.
- The public gateway is read-only. Product invocation and public write scopes require a later explicit authorization design.
- Site Intelligence remains responsible for external-source connectors, licensing, normalization, caching, and source freshness. Core governs access to those capabilities.
- Health aggregation is live and may report degraded upstream services while Core itself remains operational.
