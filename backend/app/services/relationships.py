from __future__ import annotations

from collections import deque

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..models import Entity, Relationship
from ..schemas import RelationshipCreate
from .entities import get_entity_or_404


def create_relationship(
    db: Session,
    payload: RelationshipCreate,
) -> Relationship:
    get_entity_or_404(db, payload.subject_id)
    get_entity_or_404(db, payload.object_id)

    relationship = Relationship(
        subject_id=payload.subject_id,
        predicate=payload.predicate,
        object_id=payload.object_id,
        confidence=payload.confidence,
        status=payload.status,
        provenance=payload.provenance,
    )
    db.add(relationship)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.scalar(
            select(Relationship).where(
                Relationship.subject_id == payload.subject_id,
                Relationship.predicate == payload.predicate,
                Relationship.object_id == payload.object_id,
            )
        )
        if existing is not None:
            return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relationship conflicts with an existing record.",
        ) from exc
    db.refresh(relationship)
    return relationship


def list_relationships(
    db: Session,
    *,
    subject_id: str | None,
    object_id: str | None,
    predicate: str | None,
    status_value: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Relationship], int]:
    filters = []
    if subject_id:
        filters.append(Relationship.subject_id == subject_id)
    if object_id:
        filters.append(Relationship.object_id == object_id)
    if predicate:
        filters.append(Relationship.predicate == predicate)
    if status_value:
        filters.append(Relationship.status == status_value)

    base = select(Relationship).where(*filters)
    total = db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    items = db.scalars(
        base.order_by(Relationship.predicate, Relationship.created_at)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), int(total)


def traverse_graph(
    db: Session,
    *,
    root_id: str,
    direction: str,
    max_depth: int,
    predicates: list[str] | None,
) -> tuple[list[tuple[Entity, int]], list[tuple[Relationship, int]]]:
    get_entity_or_404(db, root_id)

    visited = {root_id}
    queue = deque([(root_id, 0)])
    node_depths: dict[str, int] = {root_id: 0}
    edge_depths: dict[str, tuple[Relationship, int]] = {}

    while queue:
        current_id, current_depth = queue.popleft()
        if current_depth >= max_depth:
            continue

        filters = []
        if direction == "outbound":
            filters.append(Relationship.subject_id == current_id)
        elif direction == "inbound":
            filters.append(Relationship.object_id == current_id)
        else:
            filters.append(
                or_(
                    Relationship.subject_id == current_id,
                    Relationship.object_id == current_id,
                )
            )

        if predicates:
            filters.append(Relationship.predicate.in_(predicates))

        relationships = db.scalars(
            select(Relationship).where(*filters)
        ).all()

        for rel in relationships:
            next_depth = current_depth + 1
            edge_depths.setdefault(rel.id, (rel, next_depth))

            neighbors = []
            if rel.subject_id == current_id:
                neighbors.append(rel.object_id)
            if rel.object_id == current_id:
                neighbors.append(rel.subject_id)

            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    node_depths[neighbor_id] = next_depth
                    queue.append((neighbor_id, next_depth))

    entities = db.scalars(
        select(Entity)
        .options(selectinload(Entity.aliases))
        .where(Entity.id.in_(visited))
    ).all()
    node_records = sorted(
        ((entity, node_depths[entity.id]) for entity in entities),
        key=lambda item: (item[1], item[0].entity_type, item[0].name),
    )
    edge_records = sorted(
        edge_depths.values(),
        key=lambda item: (item[1], item[0].predicate, item[0].id),
    )
    return node_records, edge_records
