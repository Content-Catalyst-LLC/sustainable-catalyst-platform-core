from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import EvidenceFoundation, ValidationEvent
from ..schemas import (
    EvidenceFoundationCreate,
    EvidenceFoundationRead,
    ValidationEventCreate,
    ValidationEventRead,
)
from ..services.entities import get_entity_or_404

router = APIRouter(prefix="/v1", tags=["Evidence and Validation Foundations"])


@router.get(
    "/evidence-foundations",
    response_model=list[EvidenceFoundationRead],
    dependencies=[Depends(require_read)],
)
def get_evidence_foundations(
    limit: int = 50,
    db: Session = Depends(get_session),
):
    limit = max(1, min(limit, 200))
    return list(
        db.scalars(
            select(EvidenceFoundation)
            .order_by(EvidenceFoundation.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/evidence-foundations",
    response_model=EvidenceFoundationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_evidence_foundation(
    payload: EvidenceFoundationCreate,
    db: Session = Depends(get_session),
):
    if payload.subject_entity_id:
        get_entity_or_404(db, payload.subject_entity_id)
    if payload.source_entity_id:
        get_entity_or_404(db, payload.source_entity_id)
    data = payload.model_dump(exclude_none=True)
    record = EvidenceFoundation(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/validation-events",
    response_model=list[ValidationEventRead],
    dependencies=[Depends(require_read)],
)
def get_validation_events(
    limit: int = 50,
    db: Session = Depends(get_session),
):
    limit = max(1, min(limit, 200))
    return list(
        db.scalars(
            select(ValidationEvent)
            .order_by(ValidationEvent.observed_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/validation-events",
    response_model=ValidationEventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_validation_event(
    payload: ValidationEventCreate,
    db: Session = Depends(get_session),
):
    if payload.entity_id:
        get_entity_or_404(db, payload.entity_id)
    data = payload.model_dump(exclude_none=True)
    data.setdefault("observed_at", datetime.now(timezone.utc))
    record = ValidationEvent(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
