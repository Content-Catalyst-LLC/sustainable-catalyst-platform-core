from __future__ import annotations
from sqlalchemy import select
from .database import Base, Database
from .models import PredicateDefinition, SchemaMigration
from .predicate_catalog import DEFAULT_PREDICATES

MIGRATIONS = [
    ("0001", "Initial universal entity registry, relationships, aliases, evidence foundations, validation events, and import jobs."),
    ("0002", "Knowledge Graph predicate registry, relationship review records, graph indexes, and default controlled vocabulary."),
    ("0003", "Evidence Ledger claims, source snapshots, evidence records, calculation traces, provenance activities, review assignments, and tamper-evident ledger chain."),
]

def _seed_predicates(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_PREDICATES:
            if session.get(PredicateDefinition, payload["id"]) is None:
                session.add(PredicateDefinition(**payload, metadata_json={"seed":"platform-core-v2.1.0"}))
                created += 1
        session.commit()
    return created

def run_migrations(database: Database) -> list[str]:
    Base.metadata.create_all(database.engine)
    applied: list[str] = []
    with database.session_factory() as session:
        for version, description in MIGRATIONS:
            if session.get(SchemaMigration, version) is None:
                session.add(SchemaMigration(version=version, description=description))
                session.commit()
                applied.append(version)
    _seed_predicates(database)
    return applied

def migration_status(database: Database) -> dict:
    Base.metadata.create_all(database.engine)
    with database.session_factory() as session:
        applied = {row.version for row in session.scalars(select(SchemaMigration)).all()}
        predicates = len(session.scalars(select(PredicateDefinition.id)).all())
    expected = {version for version, _ in MIGRATIONS}
    return {"expected":sorted(expected),"applied":sorted(applied),"pending":sorted(expected-applied),"predicate_definitions":predicates}
