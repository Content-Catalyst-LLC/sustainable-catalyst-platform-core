# Sustainable Catalyst Platform Core v2.1.0

**Knowledge Graph and Relationship Engine**

Platform Core v2.1.0 turns the v2.0 Universal Entity Registry into a governed knowledge graph with a controlled predicate vocabulary, reviewed relationships, richer traversal, shortest paths, relationship neighborhoods, recommendations, JSON-LD records, and a first public Knowledge Explorer.

## What v2.1.0 adds

- Controlled Predicate Registry
- Subject and object entity-type constraints
- Predicate labels, descriptions, inverses, symmetry, and transitivity metadata
- Append-only relationship review records
- Approve, reject, request-changes, and restore-proposed decisions
- Confidence and status filtering
- Bounded graph traversal
- Shortest-path discovery
- Direct relationship neighborhoods
- Graph-backed recommendations
- JSON-LD entity records
- Public Knowledge Explorer at `/explorer`
- WordPress relationship and explorer shortcodes
- Expanded Python integration client
- v2.0.0-compatible migration path

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

- Knowledge Explorer: `http://127.0.0.1:8090/explorer`
- OpenAPI: `http://127.0.0.1:8090/docs`
- Predicates: `http://127.0.0.1:8090/v1/predicates`
- Statistics: `http://127.0.0.1:8090/v1/stats`

## Key endpoints

```text
GET  /v1/predicates
POST /v1/predicates
GET  /v1/graph/{entity_id}
GET  /v1/graph/{entity_id}/neighborhood
GET  /v1/graph/{entity_id}/recommendations
GET  /v1/graph/path
POST /v1/relationships/{relationship_id}/reviews
GET  /v1/relationship-reviews
GET  /v1/entities/{entity_id}/jsonld
GET  /explorer
```

## WordPress shortcodes

```text
[sc_platform_core_status]
[sc_platform_core_entity id="sc:product:workbench"]
[sc_platform_core_relationships id="sc:product:research-librarian"]
[sc_knowledge_explorer]
```

The WordPress plugin remains a thin connector. Platform Core is the authoritative registry and graph.

## Production environment

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: ./start.sh
PYTHON_VERSION=3.12.11
```

```text
SC_CORE_ENVIRONMENT=production
SC_CORE_DATABASE_URL=<Render PostgreSQL internal database URL>
SC_CORE_WRITE_API_KEY=<long random secret>
SC_CORE_CORS_ORIGINS=https://sustainablecatalyst.com
SC_CORE_PUBLIC_READS=true
SC_CORE_MAX_GRAPH_DEPTH=4
SC_CORE_PAGE_SIZE_MAX=200
SC_CORE_EXPLORER_ENABLED=true
```

## Boundaries

The graph records structured relationships and review state. It does not automatically establish truth, causal validity, legal effect, scientific consensus, or professional conclusions.

## License

MIT
