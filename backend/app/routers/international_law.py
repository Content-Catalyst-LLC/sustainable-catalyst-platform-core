from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import InternationalLawRecordRead, InternationalLawStats, PublicEnvelope
from ..services.international_law import AUTHORITY_TAXONOMY, get_record_or_404, list_records, provenance, stats

router = APIRouter(prefix="/v1/international-law", tags=["International Law and United Nations"])
public_router = APIRouter(prefix="/api/v1/international-law", tags=["Unified Public API — International Law"])


def envelope(request: Request, data, *, meta: dict | None = None) -> PublicEnvelope:
    payload_meta = {"api_version": "v1", "request_id": request.state.request_id, "documentation": "/docs#tag/Unified-Public-API-International-Law"}
    if meta:
        payload_meta.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=payload_meta)


@router.get("/records", response_model=dict, dependencies=[Depends(require_read)])
def records(record_type: str | None = None, authority_level: str | None = None, legal_body: str | None = None, country: str | None = None, subject: str | None = None, official_symbol: str | None = None, query: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_records(db, record_type=record_type, authority_level=authority_level, legal_body=legal_body, country=country, subject=subject, official_symbol=official_symbol, query=query, start=start, end=end, limit=limit, offset=offset)
    return {"items": [InternationalLawRecordRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/records/{record_id}", response_model=InternationalLawRecordRead, dependencies=[Depends(require_read)])
def record(record_id: str, db: Session = Depends(get_session)):
    return get_record_or_404(db, record_id)


@router.get("/provenance/{record_id}", response_model=dict, dependencies=[Depends(require_read)])
def record_provenance(record_id: str, db: Session = Depends(get_session)):
    return jsonable_encoder(provenance(db, get_record_or_404(db, record_id)))


@router.get("/authority-taxonomy", response_model=dict, dependencies=[Depends(require_read)])
def authority_taxonomy():
    return AUTHORITY_TAXONOMY


@router.get("/stats", response_model=InternationalLawStats, dependencies=[Depends(require_read)])
def record_stats(db: Session = Depends(get_session)):
    return stats(db)


@public_router.get("/records", response_model=PublicEnvelope)
def public_records(request: Request, record_type: str | None = None, authority_level: str | None = None, legal_body: str | None = None, country: str | None = None, subject: str | None = None, official_symbol: str | None = None, query: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_records(db, record_type=record_type, authority_level=authority_level, legal_body=legal_body, country=country, subject=subject, official_symbol=official_symbol, query=query, start=start, end=end, public_only=True, limit=limit, offset=offset)
    return envelope(request, [InternationalLawRecordRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/records/{record_id}", response_model=PublicEnvelope)
def public_record(request: Request, record_id: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    return envelope(request, InternationalLawRecordRead.model_validate(get_record_or_404(db, record_id, public_only=True)))


@public_router.get("/authority-taxonomy", response_model=PublicEnvelope)
def public_authority_taxonomy(request: Request, _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    return envelope(request, AUTHORITY_TAXONOMY)
