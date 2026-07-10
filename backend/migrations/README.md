# Migrations

## 0001 — Universal Entity Registry

Creates the initial registry and foundation records.

## 0002 — Knowledge Graph

Creates controlled predicates and relationship reviews.

## 0003 — Evidence Ledger and Provenance

Creates claims, source snapshots, provenance activities, links, calculation traces, evidence records, reviews, assignments, and the tamper-evident ledger.

## 0004 — Unified Public API and Developer Platform

Creates:

- `api_plans`
- `developer_applications`
- `api_credentials`
- `api_request_logs`
- `webhook_subscriptions`
- `webhook_events`
- `webhook_deliveries`

Migration `0004` also seeds the default API plans.

Run:

```bash
python scripts/migrate.py
```

The migration is additive. Existing entity, graph, evidence, and ledger records remain unchanged.
