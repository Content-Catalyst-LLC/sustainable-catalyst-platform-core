from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import SignatureDossier, WorkflowDefinition, WorkflowRun
from ..schemas import (
    DossierApprovalCreate,
    DossierApprovalRead,
    DossierCreate,
    DossierFinalizeRequest,
    DossierList,
    DossierRead,
    DossierRecordCreate,
    DossierRecordRead,
    DossierVerificationResult,
    WorkflowCancelRequest,
    WorkflowDefinitionRead,
    WorkflowPlatformStats,
    WorkflowRunCreate,
    WorkflowRunRead,
    WorkflowStartRequest,
    WorkflowStepTransition,
)
from ..services.workflows import (
    add_dossier_approval,
    add_dossier_record,
    cancel_workflow_run,
    create_dossier,
    create_workflow_run,
    dossier_read,
    finalize_dossier,
    get_dossier_or_404,
    get_workflow_run_or_404,
    start_workflow_run,
    transition_workflow_step,
    verify_dossier,
    workflow_platform_stats,
    workflow_run_read,
)

router = APIRouter(prefix="/v1", tags=["Signature Dossiers and Workflows"])


@router.get("/workflow-definitions", response_model=list[WorkflowDefinitionRead], dependencies=[Depends(require_read)])
def workflow_definitions(public: bool | None = None, active: bool | None = True, db: Session = Depends(get_session)):
    filters = []
    if public is not None:
        filters.append(WorkflowDefinition.public.is_(public))
    if active is not None:
        filters.append(WorkflowDefinition.active.is_(active))
    return list(db.scalars(select(WorkflowDefinition).where(*filters).order_by(WorkflowDefinition.sort_order, WorkflowDefinition.name)).all())


@router.post("/workflow-runs", response_model=WorkflowRunRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_workflow_run(payload: WorkflowRunCreate, db: Session = Depends(get_session)):
    return create_workflow_run(db, payload)


@router.get("/workflow-runs", response_model=list[WorkflowRunRead], dependencies=[Depends(require_read)])
def workflow_runs(definition_id: str | None = None, status_value: str | None = Query(default=None, alias="status"), public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if definition_id:
        filters.append(WorkflowRun.definition_id == definition_id)
    if status_value:
        filters.append(WorkflowRun.status == status_value)
    if public is not None:
        filters.append(WorkflowRun.public.is_(public))
    records = list(db.scalars(select(WorkflowRun).where(*filters).order_by(WorkflowRun.created_at.desc()).limit(limit)).all())
    return [workflow_run_read(db, item) for item in records]


@router.get("/workflow-runs/{run_id:path}", response_model=WorkflowRunRead, dependencies=[Depends(require_read)])
def workflow_run(run_id: str, db: Session = Depends(get_session)):
    return workflow_run_read(db, get_workflow_run_or_404(db, run_id))


@router.post("/workflow-runs/{run_id:path}/start", response_model=WorkflowRunRead, dependencies=[Depends(require_write)])
def post_start_workflow(run_id: str, payload: WorkflowStartRequest, db: Session = Depends(get_session)):
    return start_workflow_run(db, run_id, payload.actor, payload.reason)


@router.post("/workflow-runs/{run_id:path}/steps/{step_key}/transition", response_model=WorkflowRunRead, dependencies=[Depends(require_write)])
def post_step_transition(run_id: str, step_key: str, payload: WorkflowStepTransition, db: Session = Depends(get_session)):
    return transition_workflow_step(db, run_id, step_key, payload)


@router.post("/workflow-runs/{run_id:path}/cancel", response_model=WorkflowRunRead, dependencies=[Depends(require_write)])
def post_cancel_workflow(run_id: str, payload: WorkflowCancelRequest, db: Session = Depends(get_session)):
    return cancel_workflow_run(db, run_id, payload.actor, payload.reason)


@router.post("/dossiers", response_model=DossierRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_dossier(payload: DossierCreate, db: Session = Depends(get_session)):
    return create_dossier(db, payload)


@router.get("/dossiers", response_model=DossierList, dependencies=[Depends(require_read)])
def dossiers(request: Request, status_value: str | None = Query(default=None, alias="status"), visibility: str | None = None, workflow_run_id: str | None = None, limit: int = Query(default=50, ge=1), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    limit = min(limit, request.app.state.settings.page_size_max)
    filters = []
    if status_value:
        filters.append(SignatureDossier.status == status_value)
    if visibility:
        filters.append(SignatureDossier.visibility == visibility)
    if workflow_run_id:
        filters.append(SignatureDossier.workflow_run_id == workflow_run_id)
    stmt = select(SignatureDossier).where(*filters)
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    items = list(db.scalars(stmt.order_by(SignatureDossier.created_at.desc()).limit(limit).offset(offset)).all())
    return DossierList(items=[dossier_read(db, item) for item in items], total=total, limit=limit, offset=offset)


@router.get("/dossiers/{dossier_id:path}/verify", response_model=DossierVerificationResult, dependencies=[Depends(require_read)])
def dossier_verification(request: Request, dossier_id: str, db: Session = Depends(get_session)):
    return verify_dossier(db, dossier_id, request.app.state.settings)


@router.get("/dossiers/{dossier_id:path}/export", dependencies=[Depends(require_read)])
def dossier_export(dossier_id: str, db: Session = Depends(get_session)):
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.status not in {"finalized", "superseded"}:
        return dossier_read(db, dossier).model_dump(mode="json")
    return {"dossier": dossier_read(db, dossier).model_dump(mode="json"), "canonical_snapshot": dossier.snapshot_json}


@router.get("/dossiers/{dossier_id:path}", response_model=DossierRead, dependencies=[Depends(require_read)])
def dossier(dossier_id: str, db: Session = Depends(get_session)):
    return dossier_read(db, get_dossier_or_404(db, dossier_id))


@router.post("/dossiers/{dossier_id:path}/records", response_model=DossierRecordRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_dossier_record(request: Request, dossier_id: str, payload: DossierRecordCreate, db: Session = Depends(get_session)):
    return add_dossier_record(db, dossier_id, payload, request.app.state.settings)


@router.post("/dossiers/{dossier_id:path}/approvals", response_model=DossierApprovalRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_dossier_approval(dossier_id: str, payload: DossierApprovalCreate, db: Session = Depends(get_session)):
    return add_dossier_approval(db, dossier_id, payload)


@router.post("/dossiers/{dossier_id:path}/finalize", response_model=DossierRead, dependencies=[Depends(require_write)])
def post_finalize_dossier(request: Request, dossier_id: str, payload: DossierFinalizeRequest, db: Session = Depends(get_session)):
    return finalize_dossier(db, dossier_id, payload.signed_by, payload.actor, request.app.state.settings)


@router.get("/workflow-platform/stats", response_model=WorkflowPlatformStats, dependencies=[Depends(require_read)])
def workflow_stats(db: Session = Depends(get_session)):
    return workflow_platform_stats(db)
