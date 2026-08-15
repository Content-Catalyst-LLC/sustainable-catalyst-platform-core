# Core v2.18.0 — Observability, SLOs & Production Operations

Core v2.18.0 adds a local-first observability control plane. Request telemetry is persisted as bounded metric samples and never becomes an evidence or Truth-precedence record. Request metric persistence is fail-open: telemetry failure cannot fail the user request.

## Privacy boundary
Only the request path is persisted by automatic HTTP instrumentation; query strings are excluded. Public status is aggregate-only and does not expose request IDs, raw samples, SLO policy internals, principal context, or operator deployment metadata.

## SLO model
The initial seeded SLOs are Platform Core availability >= 99% and p95 request latency <= 1000 ms over 60 minutes, requiring at least five samples. SLO evaluation reports met, breached, or insufficient_data. It is descriptive operational state, not evidence authority.

## Deployment markers
Operators may record started, deployed, failed, rollback, or rolled_back markers with release/environment/commit metadata. Deployment records are operator-facing and not publicly exposed.

## Provider boundary
No Prometheus, Datadog, New Relic, OpenTelemetry collector, or paid monitoring provider is required. External exporters can be added later without changing the Core observability contract.
