from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..models import Entity, EntityAlias
from ..schemas import AliasCreate, EntityCreate, EntityUpdate


def get_entity_or_404(db: Session, entity_id: str) -> Entity:
    stmt = (
        select(Entity)
        .options(selectinload(Entity.aliases))
        .where(Entity.id == entity_id)
    )
    entity = db.scalar(stmt)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity not found: {entity_id}",
        )
    return entity


def create_entity(db: Session, payload: EntityCreate) -> Entity:
    entity = Entity(
        id=payload.id,
        entity_type=payload.entity_type,
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        canonical_url=str(payload.canonical_url) if payload.canonical_url else None,
        status=payload.status,
        visibility=payload.visibility,
        schema_version=payload.schema_version,
        metadata_json=payload.metadata,
    )
    for alias in payload.aliases:
        entity.aliases.append(
            EntityAlias(namespace=alias.namespace, value=alias.value)
        )
    db.add(entity)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entity ID, type/slug, or alias already exists.",
        ) from exc
    return get_entity_or_404(db, entity.id)


def upsert_entity(db: Session, payload: EntityCreate) -> tuple[Entity, bool]:
    existing = db.get(Entity, payload.id)
    created = existing is None
    if created:
        return create_entity(db, payload), True

    existing.name = payload.name
    existing.description = payload.description
    existing.canonical_url = (
        str(payload.canonical_url) if payload.canonical_url else None
    )
    existing.status = payload.status
    existing.visibility = payload.visibility
    existing.schema_version = payload.schema_version
    existing.metadata_json = payload.metadata

    current_aliases = {(a.namespace, a.value) for a in existing.aliases}
    for alias in payload.aliases:
        key = (alias.namespace, alias.value)
        if key not in current_aliases:
            existing.aliases.append(
                EntityAlias(namespace=alias.namespace, value=alias.value)
            )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entity alias conflicts with another entity.",
        ) from exc
    return get_entity_or_404(db, existing.id), False


def update_entity(db: Session, entity_id: str, payload: EntityUpdate) -> Entity:
    entity = get_entity_or_404(db, entity_id)
    changes = payload.model_dump(exclude_unset=True)
    if "canonical_url" in changes and changes["canonical_url"] is not None:
        changes["canonical_url"] = str(changes["canonical_url"])
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for field, value in changes.items():
        setattr(entity, field, value)
    db.commit()
    return get_entity_or_404(db, entity_id)


def add_alias(
    db: Session,
    entity_id: str,
    payload: AliasCreate,
) -> EntityAlias:
    get_entity_or_404(db, entity_id)
    alias = EntityAlias(
        entity_id=entity_id,
        namespace=payload.namespace,
        value=payload.value,
    )
    db.add(alias)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alias already exists.",
        ) from exc
    db.refresh(alias)
    return alias


def resolve_alias(db: Session, namespace: str, value: str) -> Entity:
    stmt = (
        select(Entity)
        .join(EntityAlias)
        .options(selectinload(Entity.aliases))
        .where(
            EntityAlias.namespace == namespace,
            EntityAlias.value == value,
        )
    )
    entity = db.scalar(stmt)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alias not found.",
        )
    return entity


def list_entities(
    db: Session,
    *,
    query: str | None,
    entity_type: str | None,
    status_value: str | None,
    visibility: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Entity], int]:
    filters = []
    if query:
        pattern = f"%{query.strip()}%"
        filters.append(
            or_(
                Entity.id.ilike(pattern),
                Entity.name.ilike(pattern),
                Entity.description.ilike(pattern),
                Entity.slug.ilike(pattern),
            )
        )
    if entity_type:
        filters.append(Entity.entity_type == entity_type)
    if status_value:
        filters.append(Entity.status == status_value)
    if visibility:
        filters.append(Entity.visibility == visibility)

    base = select(Entity).where(*filters)
    total = db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    items = db.scalars(
        base.options(selectinload(Entity.aliases))
        .order_by(Entity.entity_type, Entity.name)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), int(total)
