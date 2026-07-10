# Sustainable Catalyst Platform Core v2.0.0

**Universal Entity Registry and Knowledge Infrastructure Foundation**

Platform Core is the shared identity, relationship, provenance-foundation, validation-event, and integration layer for Sustainable Catalyst.

It establishes one stable system of record that can be used by:

- Research Librarian
- Workbench
- Decision Studio
- Site Intelligence
- WordPress
- Future Catalyst Workspace and public API clients

This release fully implements the **Universal Entity Registry**, aliases, typed relationships, graph traversal, import jobs, registry statistics, and integration clients. It also introduces versioned foundation records for the future Evidence Ledger and Trust Center without presenting either system as complete.

## Core principle

> Different interfaces, one underlying knowledge system.

## What v2.0.0 includes

- Stable `sc:<entity-type>:<slug>` identifiers
- Entity schemas for articles, concepts, sources, datasets, indicators, tools, countries, treaties, products, services, models, claims, evidence records, and other extensible types
- External aliases and identifier resolution
- Typed relationships and bounded graph traversal
- Registry search, filtering, pagination, and statistics
- Site Intelligence manifest import adapter
- Evidence foundation records
- Validation event foundation records
- Import job audit records
- Write-key protection and public-read configuration
- SQLite development storage and PostgreSQL production support
- Cross-database migration runner
- FastAPI/OpenAPI documentation
- Python integration client
- WordPress status and registry lookup plugin
- Seed manifest for the existing Sustainable Catalyst products
- Tests, GitHub Actions, Docker, and Render configuration

## Repository structure

```text
sustainable-catalyst-platform-core-v2.0.0/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── ids.py
│   │   ├── main.py
│   │   ├── migrations.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── clients/python/sc_platform_core/
│   ├── data/
│   ├── migrations/
│   ├── scripts/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh
├── wordpress-plugin/
├── docs/
├── schemas/
├── examples/
├── render.yaml
└── CHANGELOG.md
```

## Local setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
python scripts/migrate.py
python scripts/seed_registry.py

uvicorn app.main:app --reload --port 8090
```

Open:

- API documentation: `http://127.0.0.1:8090/docs`
- Health: `http://127.0.0.1:8090/health`
- Registry statistics: `http://127.0.0.1:8090/v1/stats`
- Products: `http://127.0.0.1:8090/v1/entities?entity_type=product`

## Test

```bash
cd backend
pytest -q
```

## Production environment

Recommended Render settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: ./start.sh
PYTHON_VERSION=3.12.11
```

Required environment variables:

```text
SC_CORE_ENVIRONMENT=production
SC_CORE_DATABASE_URL=<Render PostgreSQL internal database URL>
SC_CORE_WRITE_API_KEY=<long random secret>
SC_CORE_CORS_ORIGINS=https://sustainablecatalyst.com
SC_CORE_PUBLIC_READS=true
```

The service refuses unauthenticated writes in production when no write key is configured.

## Write authentication

Send the write key in:

```http
X-SC-API-Key: your-secret
```

Read routes can remain public. Write routes are protected.

## Example entity

```json
{
  "id": "sc:product:workbench",
  "entity_type": "product",
  "slug": "workbench",
  "name": "Sustainable Catalyst Workbench",
  "description": "Calculation, modeling, visualization, validation, and article-embedded tool environment.",
  "canonical_url": "https://sustainablecatalyst.com/modeling-analytics/workbench/",
  "status": "active",
  "visibility": "public",
  "schema_version": "1.0",
  "metadata": {
    "platform_role": "analysis_engine"
  }
}
```

## Example relationship

```json
{
  "subject_id": "sc:product:decision-studio",
  "predicate": "uses",
  "object_id": "sc:product:workbench",
  "confidence": 1.0,
  "status": "verified",
  "provenance": {
    "source": "platform-architecture"
  }
}
```

## Boundaries

Platform Core is infrastructure for identification, interoperability, provenance, and review. It does not automatically verify truth, certify compliance, establish professional conclusions, or replace accountable human review.

## License

MIT
