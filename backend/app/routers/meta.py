from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read
from ..models import (
    Entity,
    EntityAlias,
    EvidenceFoundation,
    ImportJob,
    Relationship,
    ValidationEvent,
)
from ..schemas import MetaResponse, RegistryStats

router = APIRouter(tags=["Service"])


@router.get("/health")
def health(request: Request):
    return {
        "ok": True,
        "service": request.app.state.settings.app_name,
        "version": request.app.state.settings.version,
        "environment": request.app.state.settings.environment,
    }


@router.get("/ready")
def ready(db: Session = Depends(get_session)):
    db.execute(text("SELECT 1"))
    return {"ok": True, "database": "ready"}


@router.get(
    "/v1/meta",
    response_model=MetaResponse,
    dependencies=[Depends(require_read)],
)
def meta(request: Request):
    settings = request.app.state.settings
    return MetaResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        public_reads=settings.public_reads,
        write_auth_configured=bool(settings.write_api_key),
        max_graph_depth=settings.max_graph_depth,
        capabilities=[
            "universal_entity_registry",
            "entity_alias_resolution",
            "typed_relationships",
            "bounded_graph_traversal",
            "site_intelligence_manifest_import",
            "evidence_foundation_records",
            "validation_event_foundation",
            "openapi",
            "python_client",
            "wordpress_client",
        ],
        deferred_capabilities=[
            "full_evidence_ledger",
            "public_trust_center",
            "public_api_key_issuance",
            "visual_knowledge_explorer",
            "user_casebooks",
        ],
    )


@router.get(
    "/v1/stats",
    response_model=RegistryStats,
    dependencies=[Depends(require_read)],
)
def stats(db: Session = Depends(get_session)):
    entity_rows = db.execute(
        select(Entity.entity_type, func.count(Entity.id))
        .group_by(Entity.entity_type)
        .order_by(Entity.entity_type)
    ).all()
    relationship_rows = db.execute(
        select(Relationship.predicate, func.count(Relationship.id))
        .group_by(Relationship.predicate)
        .order_by(Relationship.predicate)
    ).all()

    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    return RegistryStats(
        entities=count(Entity),
        relationships=count(Relationship),
        aliases=count(EntityAlias),
        evidence_foundations=count(EvidenceFoundation),
        validation_events=count(ValidationEvent),
        import_jobs=count(ImportJob),
        entities_by_type={key: int(value) for key, value in entity_rows},
        relationships_by_predicate={
            key: int(value) for key, value in relationship_rows
        },
    )
