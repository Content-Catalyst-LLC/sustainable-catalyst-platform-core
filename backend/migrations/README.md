# Migrations

## 0001 — Universal Entity Registry

Creates the initial registry and foundation records.

## 0002 — Knowledge Graph

Creates controlled predicates and relationship reviews.

## 0003 — Evidence Ledger and Provenance

Creates claims, source snapshots, provenance activities, links, calculation traces, evidence records, reviews, assignments, and the tamper-evident ledger.

## 0004 — Unified Public API and Developer Platform

Creates API plans, developer applications, hashed credentials, request logs, webhook subscriptions, events, and deliveries.

## 0005 — Trust Center and Evaluation Framework

Creates:

- `evaluation_definitions`
- `evaluation_runs`
- `evaluation_check_results`
- `trust_findings`
- `trust_incidents`
- `known_limitations`
- `trust_attestations`

Migration `0005` seeds the default evaluation registry and merges the `trust:read` scope into existing API plans without replacing their quota settings.

Run:

```bash
python scripts/migrate.py
```

The migration is additive. Existing registry, graph, evidence, ledger, developer, and webhook records remain unchanged.

## 0006 — Signature Dossiers and End-to-End Workflows

Creates:

- `workflow_definitions`
- `workflow_runs`
- `workflow_steps`
- `workflow_transitions`
- `signature_dossiers`
- `dossier_records`
- `dossier_approvals`

Migration `0006` also seeds the three default workflow definitions and updates existing API plans with `workflow:read` and `dossier:read`.
