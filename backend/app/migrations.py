from __future__ import annotations
from sqlalchemy import select
from .database import Base, Database
from .models import ApiPlan, EvaluationDefinition, PredicateDefinition, SchemaMigration
from .predicate_catalog import DEFAULT_PREDICATES
from .api_plan_catalog import DEFAULT_API_PLANS
from .evaluation_catalog import DEFAULT_EVALUATION_DEFINITIONS

MIGRATIONS = [
    ("0001", "Initial universal entity registry, relationships, aliases, evidence foundations, validation events, and import jobs."),
    ("0002", "Knowledge Graph predicate registry, relationship review records, graph indexes, and default controlled vocabulary."),
    ("0003", "Evidence Ledger claims, source snapshots, evidence records, calculation traces, provenance activities, review assignments, and tamper-evident ledger chain."),
    ("0004", "Unified Public API plans, developer applications, hashed credentials, request usage records, webhooks, and developer portal infrastructure."),
    ("0005", "Trust Center evaluation definitions, immutable evaluation runs and checks, findings, incidents, known limitations, attestations, and public trust status."),
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

def _seed_api_plans(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_API_PLANS:
            existing = session.get(ApiPlan, payload["id"])
            if existing is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(ApiPlan(**data, metadata_json=metadata))
                created += 1
            else:
                existing.allowed_scopes = sorted(
                    set(existing.allowed_scopes or [])
                    | set(payload.get("allowed_scopes", []))
                )
                session.add(existing)
        session.commit()
    return created


def _seed_evaluation_definitions(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_EVALUATION_DEFINITIONS:
            if session.get(EvaluationDefinition, payload["id"]) is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(EvaluationDefinition(**data, metadata_json=metadata))
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
    _seed_api_plans(database)
    _seed_evaluation_definitions(database)
    return applied

def migration_status(database: Database) -> dict:
    Base.metadata.create_all(database.engine)
    with database.session_factory() as session:
        applied = {row.version for row in session.scalars(select(SchemaMigration)).all()}
        predicates = len(session.scalars(select(PredicateDefinition.id)).all())
        api_plans = len(session.scalars(select(ApiPlan.id)).all())
        evaluation_definitions = len(session.scalars(select(EvaluationDefinition.id)).all())
    expected = {version for version, _ in MIGRATIONS}
    return {"expected":sorted(expected),"applied":sorted(applied),"pending":sorted(expected-applied),"predicate_definitions":predicates,"api_plans":api_plans,"evaluation_definitions":evaluation_definitions}
