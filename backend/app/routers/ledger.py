from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read
from ..models import LedgerEntry
from ..schemas import LedgerEntryRead, LedgerVerificationResult
from ..services.ledger import list_ledger_entries, verify_ledger

router = APIRouter(prefix="/v1/ledger", tags=["Tamper-Evident Ledger"])


@router.get(
    "/entries",
    response_model=list[LedgerEntryRead],
    dependencies=[Depends(require_read)],
)
def get_ledger_entries(
    record_type: str | None = None,
    record_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    return list_ledger_entries(
        db,
        record_type=record_type,
        record_id=record_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/verify",
    response_model=LedgerVerificationResult,
    dependencies=[Depends(require_read)],
)
def get_ledger_verification(db: Session = Depends(get_session)):
    return verify_ledger(db)


@router.get(
    "/head",
    response_model=LedgerEntryRead | None,
    dependencies=[Depends(require_read)],
)
def get_ledger_head(db: Session = Depends(get_session)):
    return db.scalar(
        select(LedgerEntry)
        .order_by(LedgerEntry.sequence.desc())
        .limit(1)
    )
