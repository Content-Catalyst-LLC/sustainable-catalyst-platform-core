# Migrations

## 0001 — v2.0.0

Creates the universal registry, aliases, relationships, evidence foundations, validation events, import jobs, and migration ledger.

## 0002 — v2.1.0

Creates and seeds:

- `predicate_definitions`
- `relationship_reviews`
- controlled predicate vocabulary
- graph-oriented indexes

Run:

```bash
python scripts/migrate.py
```

The migration adds graph governance without changing existing Sustainable Catalyst entity IDs.
