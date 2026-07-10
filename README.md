# Sustainable Catalyst Platform Core v2.2.0

**Evidence Ledger and Provenance Records**

Platform Core v2.2.0 adds a mature evidence and provenance layer to the Universal Entity Registry and governed Knowledge Graph.

The release records:

- Claims
- Immutable source snapshots
- Supporting, contradicting, contextual, and neutral evidence
- Workbench calculation traces
- Provenance activities and links
- Evidence review assignments
- Append-only review decisions
- Exportable evidence manifests
- Tamper-evident ledger entries
- Full ledger-chain verification

## Architectural principle

> Evidence must remain connected to the claim, source, method, calculation, reviewer, and system that produced or evaluated it.

## What v2.2.0 adds

### Claim registry

Claims can be attached to Platform Core entities and assigned:

- Claim type
- Lifecycle status
- Visibility
- Language
- Extensible metadata

Claim creation and revision generate ledger entries.

### Immutable source snapshots

A source snapshot records:

- Canonical URL
- Source entity
- Title and publisher
- Publication and retrieval times
- Media type
- SHA-256 content hash
- Content length
- Short excerpt
- Archive or storage references
- Metadata

The full supplied content is used to compute the hash but is not returned through the public API. Full snapshot bodies can later be stored through an object-storage adapter.

### Evidence records

Evidence can connect a claim or subject to:

- A source entity
- A source snapshot
- A graph relationship
- A Workbench calculation trace

Evidence records carry:

- Evidence type
- Stance
- Statement
- Methodology
- Confidence
- Review status
- Provenance metadata

### Calculation traces

Calculation traces preserve:

- Tool entity ID
- Inputs and outputs
- Formula version
- Code version
- Runtime environment
- Run ID
- Content hash
- Provenance activity

### Provenance records

Activities identify:

- What process occurred
- Who or what agent performed it
- What software was used
- Parameters and environment
- Start and end times
- Status

Typed provenance links record what an activity used, generated, derived from, or was informed by.

### Review workflow

Evidence can be assigned to reviewers and reviewed through append-only decisions:

- Approve
- Reject
- Needs changes
- Restore to unreviewed

Every assignment, completion, and review decision is recorded in the ledger.

### Tamper-evident ledger

Every material evidence operation appends a chained SHA-256 entry containing:

- Sequence
- Record type and ID
- Action
- Actor
- Canonical payload hash
- Previous entry hash
- Entry hash
- Timestamp

Ledger entries cannot be updated or deleted through the ORM. The verification endpoint recalculates payload and entry hashes and validates the entire chain.

This is tamper-evident infrastructure, not a blockchain and not a substitute for database security, backups, access controls, or independent archival systems.

## Local setup

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
.venv/bin/python scripts/migrate.py
.venv/bin/python scripts/seed_registry.py

.venv/bin/python -m uvicorn app.main:app --reload --port 8090
```

Open:

- Evidence Explorer: `http://127.0.0.1:8090/evidence-explorer`
- Knowledge Explorer: `http://127.0.0.1:8090/explorer`
- OpenAPI: `http://127.0.0.1:8090/docs`
- Ledger verification: `http://127.0.0.1:8090/v1/ledger/verify`
- Evidence statistics: `http://127.0.0.1:8090/v1/evidence/stats`

## Key API routes

```text
POST /v1/claims
GET  /v1/claims
GET  /v1/claims/{claim_id}
PATCH /v1/claims/{claim_id}

POST /v1/source-snapshots
GET  /v1/source-snapshots
POST /v1/source-snapshots/{snapshot_id}/verify

POST /v1/provenance/activities
POST /v1/provenance/activities/{activity_id}/links

POST /v1/calculation-traces
GET  /v1/calculation-traces/{trace_id}

POST /v1/evidence-records
GET  /v1/evidence-records
POST /v1/evidence-records/{evidence_id}/reviews
POST /v1/evidence-records/{evidence_id}/assignments

GET  /v1/evidence/manifests/{claim_id}
GET  /v1/evidence/stats

GET  /v1/ledger/entries
GET  /v1/ledger/head
GET  /v1/ledger/verify
```

## Example claim

```json
{
  "actor": "decision-studio",
  "claim_text": "The proposed intervention reduces annual emissions.",
  "claim_type": "analytical",
  "subject_entity_id": "sc:concept:emissions-reduction",
  "status": "draft",
  "visibility": "public",
  "language": "en",
  "metadata": {}
}
```

## Example source snapshot

```json
{
  "actor": "site-intelligence",
  "source_entity_id": "sc:source:example",
  "canonical_url": "https://example.org/report",
  "media_type": "text/plain",
  "content": "Canonical captured source content.",
  "metadata": {}
}
```

## Example evidence record

```json
{
  "actor": "decision-studio",
  "evidence_type": "source-record",
  "stance": "supports",
  "claim_id": "sc:claim:...",
  "source_snapshot_id": "sc:snapshot:...",
  "statement": "The captured source supports the claim.",
  "confidence": 0.84,
  "review_status": "unreviewed",
  "provenance": {},
  "metadata": {}
}
```

## Evidence manifests

A manifest packages the complete available evidence context for a claim:

- Claim
- Evidence records
- Source snapshots
- Calculation traces
- Provenance activities and links
- Reviews
- Review assignments
- Relevant ledger entries
- Manifest hash

The manifest hash is recalculated from the canonical package contents.

## WordPress shortcodes

```text
[sc_platform_core_status]
[sc_platform_core_entity id="sc:product:workbench"]
[sc_platform_core_relationships id="sc:product:research-librarian"]
[sc_knowledge_explorer]

[sc_evidence_ledger_status]
[sc_evidence_manifest claim_id="sc:claim:..."]
[sc_evidence_explorer]
```

The WordPress plugin remains a thin connector. The authoritative ledger remains in Platform Core.

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
SC_CORE_EVIDENCE_EXPLORER_ENABLED=true
SC_CORE_SNAPSHOT_EXCERPT_MAX=1200
```

## Boundaries

The Evidence Ledger records what evidence was entered, linked, reviewed, transformed, or calculated. It does not automatically determine truth, scientific validity, legal admissibility, professional compliance, or the reliability of a source.

## License

MIT
