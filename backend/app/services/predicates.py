from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import PredicateDefinition
from ..schemas import PredicateCreate, PredicateUpdate

def get_predicate_or_404(db: Session, predicate_id: str) -> PredicateDefinition:
    predicate = db.get(PredicateDefinition, predicate_id)
    if predicate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Predicate not found: {predicate_id}")
    return predicate

def list_predicates(db: Session, *, status_value: str | None, visibility: str | None):
    filters = []
    if status_value:
        filters.append(PredicateDefinition.status == status_value)
    if visibility:
        filters.append(PredicateDefinition.visibility == visibility)
    stmt = select(PredicateDefinition).where(*filters)
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    items = db.scalars(stmt.order_by(PredicateDefinition.sort_order, PredicateDefinition.label)).all()
    return list(items), total

def create_predicate(db: Session, payload: PredicateCreate) -> PredicateDefinition:
    data = payload.model_dump()
    data["metadata_json"] = data.pop("metadata")
    predicate = PredicateDefinition(**data)
    db.add(predicate)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Predicate already exists.") from exc
    db.refresh(predicate)
    return predicate

def update_predicate(db: Session, predicate_id: str, payload: PredicateUpdate) -> PredicateDefinition:
    predicate = get_predicate_or_404(db, predicate_id)
    changes = payload.model_dump(exclude_unset=True)
    if "metadata" in changes:
        changes["metadata_json"] = changes.pop("metadata")
    for key, value in changes.items():
        setattr(predicate, key, value)
    db.commit()
    db.refresh(predicate)
    return predicate

def validate_predicate_usage(db: Session, *, predicate_id: str, subject_type: str, object_type: str) -> PredicateDefinition:
    predicate = get_predicate_or_404(db, predicate_id)
    if predicate.status != "active":
        raise HTTPException(status_code=422, detail=f"Predicate is not active: {predicate_id}")
    if predicate.allowed_subject_types and subject_type not in predicate.allowed_subject_types:
        raise HTTPException(status_code=422, detail=f"Predicate {predicate_id} does not allow subject type {subject_type}.")
    if predicate.allowed_object_types and object_type not in predicate.allowed_object_types:
        raise HTTPException(status_code=422, detail=f"Predicate {predicate_id} does not allow object type {object_type}.")
    return predicate
