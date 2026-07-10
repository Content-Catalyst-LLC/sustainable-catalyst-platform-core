# Migrations

## 0001 — Universal Entity Registry

Creates the v2.0.0 registry and foundation tables.

## 0002 — Knowledge Graph

Creates predicate definitions and relationship reviews.

## 0003 — Evidence Ledger and Provenance

Creates:

- `claim_records`
- `source_snapshots`
- `provenance_activities`
- `provenance_links`
- `calculation_traces`
- `evidence_records`
- `evidence_reviews`
- `evidence_review_assignments`
- `ledger_entries`

Run:

```bash
python scripts/migrate.py
```

Migration 0003 adds new tables without changing existing entity IDs, graph relationships, or v2.0/v2.1 API records.
