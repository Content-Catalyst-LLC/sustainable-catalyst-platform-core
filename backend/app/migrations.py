from __future__ import annotations
from sqlalchemy import select
from .database import Base, Database
from .models import ApiPlan, EvaluationDefinition, LiveDataConnector, LiveDataSource, PredicateDefinition, SchemaMigration, WorkflowDefinition
from .predicate_catalog import DEFAULT_PREDICATES
from .api_plan_catalog import DEFAULT_API_PLANS
from .evaluation_catalog import DEFAULT_EVALUATION_DEFINITIONS
from .workflow_catalog import DEFAULT_WORKFLOW_DEFINITIONS
from .live_data_catalog import DEFAULT_LIVE_DATA_CONNECTORS, DEFAULT_LIVE_DATA_SOURCES

MIGRATIONS = [
    ("0001", "Initial universal entity registry, relationships, aliases, evidence foundations, validation events, and import jobs."),
    ("0002", "Knowledge Graph predicate registry, relationship review records, graph indexes, and default controlled vocabulary."),
    ("0003", "Evidence Ledger claims, source snapshots, evidence records, calculation traces, provenance activities, review assignments, and tamper-evident ledger chain."),
    ("0004", "Unified Public API plans, developer applications, hashed credentials, request usage records, webhooks, and developer portal infrastructure."),
    ("0005", "Trust Center evaluation definitions, immutable evaluation runs and checks, findings, incidents, known limitations, attestations, and public trust status."),
    ("0006", "Signature dossiers, frozen record snapshots, approvals, platform signatures, workflow definitions, runs, steps, and append-only transitions."),
    ("0007", "Free live-data source registry, connector definitions, ingestion runs, bounded raw records, normalized observations, freshness, and provenance."),
    ("0008", "International-law and United Nations connector pack, dedicated legal-authority records, official-document provenance, and public discovery APIs."),
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

def _seed_workflow_definitions(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_WORKFLOW_DEFINITIONS:
            existing = session.get(WorkflowDefinition, payload["id"])
            if existing is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(WorkflowDefinition(**data, metadata_json=metadata))
                created += 1
            else:
                existing.stages = payload["stages"]
                existing.version = payload.get("version", existing.version)
                existing.active = payload.get("active", existing.active)
                existing.public = payload.get("public", existing.public)
                session.add(existing)
        session.commit()
    return created



def _seed_live_data_registry(database: Database) -> tuple[int, int]:
    sources_created = 0
    connectors_created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_LIVE_DATA_SOURCES:
            existing = session.get(LiveDataSource, payload["id"])
            data = dict(payload)
            metadata = data.pop("metadata", {})
            if existing is None:
                session.add(LiveDataSource(**data, metadata_json=metadata))
                sources_created += 1
        session.flush()
        for payload in DEFAULT_LIVE_DATA_CONNECTORS:
            existing = session.get(LiveDataConnector, payload["id"])
            data = dict(payload)
            configuration = data.pop("configuration", {})
            if existing is None:
                session.add(LiveDataConnector(**data, configuration_json=configuration))
                connectors_created += 1
        session.commit()
    return sources_created, connectors_created

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
    _seed_workflow_definitions(database)
    _seed_live_data_registry(database)
    return applied

def migration_status(database: Database) -> dict:
    Base.metadata.create_all(database.engine)
    with database.session_factory() as session:
        applied = {row.version for row in session.scalars(select(SchemaMigration)).all()}
        predicates = len(session.scalars(select(PredicateDefinition.id)).all())
        api_plans = len(session.scalars(select(ApiPlan.id)).all())
        evaluation_definitions = len(session.scalars(select(EvaluationDefinition.id)).all())
        workflow_definitions = len(session.scalars(select(WorkflowDefinition.id)).all())
        live_data_sources = len(session.scalars(select(LiveDataSource.id)).all())
        live_data_connectors = len(session.scalars(select(LiveDataConnector.id)).all())
    expected = {version for version, _ in MIGRATIONS}
    return {"expected":sorted(expected),"applied":sorted(applied),"pending":sorted(expected-applied),"predicate_definitions":predicates,"api_plans":api_plans,"evaluation_definitions":evaluation_definitions,"workflow_definitions":workflow_definitions,"live_data_sources":live_data_sources,"live_data_connectors":live_data_connectors}
