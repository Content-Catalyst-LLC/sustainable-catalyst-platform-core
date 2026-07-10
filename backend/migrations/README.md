# Migrations

Platform Core v2.0.0 uses a small cross-database migration ledger implemented in `app/migrations.py`.

The initial migration creates:

- `entities`
- `entity_aliases`
- `relationships`
- `evidence_foundations`
- `validation_events`
- `import_jobs`
- `schema_migrations`

Run:

```bash
python scripts/migrate.py
```

Future versions should append a migration version and an explicit migration function. Never rewrite a migration after release.
