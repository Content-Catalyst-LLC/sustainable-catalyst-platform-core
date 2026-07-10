from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import ImportJob
from ..schemas import ImportJobRead, SiteIntelligenceManifest
from ..services.imports import import_site_intelligence_manifest

router = APIRouter(prefix="/v1/imports", tags=["Imports"])


@router.post(
    "/site-intelligence",
    response_model=ImportJobRead,
    dependencies=[Depends(require_write)],
)
def post_site_intelligence_import(
    payload: SiteIntelligenceManifest,
    db: Session = Depends(get_session),
):
    return import_site_intelligence_manifest(db, payload)


@router.get(
    "",
    response_model=list[ImportJobRead],
    dependencies=[Depends(require_read)],
)
def get_import_jobs(
    limit: int = 50,
    db: Session = Depends(get_session),
):
    limit = max(1, min(limit, 200))
    return list(
        db.scalars(
            select(ImportJob)
            .order_by(ImportJob.started_at.desc())
            .limit(limit)
        ).all()
    )
