# Streaming, Alerts, and Source Reliability — Core v2.9.0

Core v2.9.0 adds a persistent reliability plane around the existing governed connector gateway.

## Design boundaries

1. External provider uptime is observable but is not a release-promotion dependency.
2. A successful source ingestion is never rolled back because an alert or stream event could not be emitted.
3. Provider failover is explicit. Core does not decide that two sources are semantically interchangeable merely because they share a domain.
4. Replay is append-only: a dead-letter record remains part of history and replay creates a new queued work item.
5. Public SSE contains only events marked public and still uses the scoped public API credential boundary.

## Persistent worker queue

`connector_work_items` stores connector ID, credential-stripped parameters, priority, attempts, lease ownership, lease expiry, execution connector, ingestion run, and completion state. API keys, tokens, passwords, authorization values, and other credential-like parameters are removed before persistence; connector credentials belong in deployment settings. Workers claim the next available item by priority and creation time. Expired leases return to pending state.

The standalone worker is:

```bash
python backend/scripts/run_connector_worker.py
```

Use `--once` for deployment verification or cron-style execution.

## Server-Sent Events

Internal stream:

```text
GET /v1/reliability/stream
```

Scoped public stream:

```text
GET /api/v1/reliability/stream
```

Both support `after_id` and `event_type`, and standard `Last-Event-ID` resume semantics. `once=true` returns a deterministic snapshot and closes, which is useful for tests and operational probes.

## Alerts

Alert rules can filter by domain, metric, connector, source, numeric comparison, and an optional point-in-bounding-box geography. Supported operators are `exists`, `gt`, `gte`, `lt`, `lte`, `eq`, and `neq`.

A triggered alert becomes a persisted `alert.triggered` stream event. The event keeps the rule ID, severity, source, connector, metric, value, unit, and observation time.

## Stale-source detection

A connector is `stale` when `last_success_at` exceeds its declared `freshness_window_seconds`. A connector with no successful ingestion is `never_succeeded`. These states are visible independently from configuration status.

## Dead letters and replay

When a work item reaches `max_attempts`, Core marks the work item `dead_letter` and writes an immutable `dead_letter_records` entry. Replaying a record increments replay metadata and creates a new pending work item.

## Provider failover

Connectors can opt into an explicit group with configuration values:

```json
{
  "failover_group": "provider-family-name",
  "failover_priority": 10,
  "failover_parameters_compatible": true
}
```

Resolution considers connector enablement, configuration state, health state, and priority. Automatic worker failover only passes the same request parameters to a backup when `failover_parameters_compatible` is explicitly true. Without an explicit group, Core evaluates only the requested connector.

## Release semantics

`/ready` continues to represent first-party production integration readiness. The reliability plane is reported there, but transient third-party provider health and stale-source counts do not independently block the Core release gate.
