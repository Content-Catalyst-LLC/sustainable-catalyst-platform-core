from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..dependencies import get_session
from ..models import SignatureDossier, WorkflowDefinition
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services.workflows import dossier_read, get_dossier_or_404, get_workflow_run_or_404, verify_dossier, workflow_run_read

router = APIRouter(prefix="/api/v1", tags=["Public Signature Dossiers and Workflows"])


def envelope(request: Request, data, meta: dict | None = None):
    values = {"api_version": "v1", "request_id": request.state.request_id, "documentation": "/developers"}
    if meta:
        values.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=values)


@router.get("/workflow-definitions", response_model=PublicEnvelope)
def public_workflow_definitions(request: Request, _context: PublicApiContext = Depends(require_public_scope("workflow:read")), db: Session = Depends(get_session)):
    records = list(db.scalars(select(WorkflowDefinition).where(WorkflowDefinition.public.is_(True), WorkflowDefinition.active.is_(True)).order_by(WorkflowDefinition.sort_order)).all())
    return envelope(request, records)


@router.get("/workflow-runs/{run_id:path}", response_model=PublicEnvelope)
def public_workflow_run(request: Request, run_id: str, _context: PublicApiContext = Depends(require_public_scope("workflow:read")), db: Session = Depends(get_session)):
    run = get_workflow_run_or_404(db, run_id)
    if not run.public:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    return envelope(request, workflow_run_read(db, run))


@router.get("/dossiers", response_model=PublicEnvelope)
def public_dossiers(request: Request, limit: int = Query(default=50, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("dossier:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    filters = [SignatureDossier.visibility == "public", SignatureDossier.status.in_(["finalized", "superseded"])]
    total = int(db.scalar(select(func.count()).select_from(SignatureDossier).where(*filters)) or 0)
    records = list(db.scalars(select(SignatureDossier).where(*filters).order_by(SignatureDossier.signed_at.desc()).limit(limit).offset(offset)).all())
    return envelope(request, [dossier_read(db, item, include_private_records=False) for item in records], {"pagination": {"total": total, "limit": limit, "offset": offset}})


@router.get("/dossiers/{dossier_id:path}/verify", response_model=PublicEnvelope)
def public_dossier_verify(request: Request, dossier_id: str, _context: PublicApiContext = Depends(require_public_scope("dossier:read")), db: Session = Depends(get_session)):
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.visibility != "public" or dossier.status not in {"finalized", "superseded"}:
        raise HTTPException(status_code=404, detail="Dossier not found.")
    return envelope(request, verify_dossier(db, dossier_id, request.app.state.settings))


@router.get("/dossiers/{dossier_id:path}", response_model=PublicEnvelope)
def public_dossier(request: Request, dossier_id: str, _context: PublicApiContext = Depends(require_public_scope("dossier:read")), db: Session = Depends(get_session)):
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.visibility != "public" or dossier.status not in {"finalized", "superseded"}:
        raise HTTPException(status_code=404, detail="Dossier not found.")
    data = dossier_read(db, dossier, include_private_records=False).model_dump(mode="json")
    if dossier.snapshot_json:
        data["canonical_snapshot"] = {**dossier.snapshot_json, "records": [item for item in dossier.snapshot_json.get("records", []) if item.get("public", True)]}
    return envelope(request, data)
