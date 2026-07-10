from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import EvaluationCheckResult, EvaluationDefinition, EvaluationRun, KnownLimitation, TrustAttestation, TrustFinding, TrustIncident
from ..schemas import (
    EvaluationDefinitionCreate,
    EvaluationDefinitionRead,
    EvaluationDefinitionUpdate,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationSuiteRequest,
    EvaluationSuiteResult,
    KnownLimitationCreate,
    KnownLimitationRead,
    KnownLimitationUpdate,
    TrustAttestationCreate,
    TrustAttestationRead,
    TrustAttestationRevoke,
    TrustFindingCreate,
    TrustFindingRead,
    TrustFindingUpdate,
    TrustIncidentCreate,
    TrustIncidentRead,
    TrustIncidentUpdate,
    TrustStatusResponse,
)
from ..services.trust import (
    build_trust_status,
    create_attestation,
    create_definition,
    create_finding,
    create_incident,
    create_limitation,
    evaluation_run_read,
    get_attestation_or_404,
    get_definition_or_404,
    get_finding_or_404,
    get_incident_or_404,
    get_limitation_or_404,
    get_run_or_404,
    revoke_attestation,
    run_evaluation,
    run_suite,
    update_definition,
    update_finding,
    update_incident,
    update_limitation,
)

router = APIRouter(prefix="/v1/trust", tags=["Trust Center Administration"])


@router.get("/status", response_model=TrustStatusResponse, dependencies=[Depends(require_read)])
def trust_status(request: Request, db: Session = Depends(get_session)):
    return build_trust_status(db, request.app.state.settings, public_only=False)


@router.get("/definitions", response_model=list[EvaluationDefinitionRead], dependencies=[Depends(require_read)])
def definitions(domain: str | None = None, active: bool | None = None, public: bool | None = None, db: Session = Depends(get_session)):
    filters = []
    if domain: filters.append(EvaluationDefinition.domain == domain)
    if active is not None: filters.append(EvaluationDefinition.active.is_(active))
    if public is not None: filters.append(EvaluationDefinition.public.is_(public))
    return list(db.scalars(select(EvaluationDefinition).where(*filters).order_by(EvaluationDefinition.sort_order, EvaluationDefinition.name)).all())


@router.post("/definitions", response_model=EvaluationDefinitionRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_definition(payload: EvaluationDefinitionCreate, db: Session = Depends(get_session)):
    return create_definition(db, payload)


@router.get("/definitions/{definition_id}", response_model=EvaluationDefinitionRead, dependencies=[Depends(require_read)])
def definition(definition_id: str, db: Session = Depends(get_session)):
    return get_definition_or_404(db, definition_id)


@router.patch("/definitions/{definition_id}", response_model=EvaluationDefinitionRead, dependencies=[Depends(require_write)])
def patch_definition(definition_id: str, payload: EvaluationDefinitionUpdate, db: Session = Depends(get_session)):
    return update_definition(db, definition_id, payload)


@router.post("/definitions/{definition_id}/runs", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_run(request: Request, definition_id: str, payload: EvaluationRunCreate, db: Session = Depends(get_session)):
    return run_evaluation(db, definition_id, payload, request.app.state.settings)


@router.post("/run-suite", response_model=EvaluationSuiteResult, dependencies=[Depends(require_write)])
def post_suite(request: Request, payload: EvaluationSuiteRequest, db: Session = Depends(get_session)):
    return run_suite(db, payload, request.app.state.settings)


@router.get("/runs", response_model=list[EvaluationRunRead], dependencies=[Depends(require_read)])
def runs(definition_id: str | None = None, target_entity_id: str | None = None, status_value: str | None = Query(default=None, alias="status"), public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if definition_id: filters.append(EvaluationRun.definition_id == definition_id)
    if target_entity_id: filters.append(EvaluationRun.target_entity_id == target_entity_id)
    if status_value: filters.append(EvaluationRun.status == status_value)
    if public is not None: filters.append(EvaluationRun.public.is_(public))
    records = list(db.scalars(select(EvaluationRun).where(*filters).order_by(EvaluationRun.completed_at.desc()).limit(limit)).all())
    return [evaluation_run_read(db, record) for record in records]


@router.get("/runs/{run_id:path}", response_model=EvaluationRunRead, dependencies=[Depends(require_read)])
def run(run_id: str, db: Session = Depends(get_session)):
    return evaluation_run_read(db, get_run_or_404(db, run_id))


@router.get("/findings", response_model=list[TrustFindingRead], dependencies=[Depends(require_read)])
def findings(status_value: str | None = Query(default=None, alias="status"), severity: str | None = None, public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if status_value: filters.append(TrustFinding.status == status_value)
    if severity: filters.append(TrustFinding.severity == severity)
    if public is not None: filters.append(TrustFinding.public.is_(public))
    return list(db.scalars(select(TrustFinding).where(*filters).order_by(TrustFinding.created_at.desc()).limit(limit)).all())


@router.post("/findings", response_model=TrustFindingRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_finding(payload: TrustFindingCreate, db: Session = Depends(get_session)):
    return create_finding(db, payload)


@router.get("/findings/{finding_id:path}", response_model=TrustFindingRead, dependencies=[Depends(require_read)])
def finding(finding_id: str, db: Session = Depends(get_session)):
    return get_finding_or_404(db, finding_id)


@router.patch("/findings/{finding_id:path}", response_model=TrustFindingRead, dependencies=[Depends(require_write)])
def patch_finding(finding_id: str, payload: TrustFindingUpdate, db: Session = Depends(get_session)):
    return update_finding(db, finding_id, payload)


@router.get("/incidents", response_model=list[TrustIncidentRead], dependencies=[Depends(require_read)])
def incidents(status_value: str | None = Query(default=None, alias="status"), public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if status_value: filters.append(TrustIncident.status == status_value)
    if public is not None: filters.append(TrustIncident.public.is_(public))
    return list(db.scalars(select(TrustIncident).where(*filters).order_by(TrustIncident.started_at.desc()).limit(limit)).all())


@router.post("/incidents", response_model=TrustIncidentRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_incident(payload: TrustIncidentCreate, db: Session = Depends(get_session)):
    return create_incident(db, payload)


@router.get("/incidents/{incident_id:path}", response_model=TrustIncidentRead, dependencies=[Depends(require_read)])
def incident(incident_id: str, db: Session = Depends(get_session)):
    return get_incident_or_404(db, incident_id)


@router.patch("/incidents/{incident_id:path}", response_model=TrustIncidentRead, dependencies=[Depends(require_write)])
def patch_incident(incident_id: str, payload: TrustIncidentUpdate, db: Session = Depends(get_session)):
    return update_incident(db, incident_id, payload)


@router.get("/limitations", response_model=list[KnownLimitationRead], dependencies=[Depends(require_read)])
def limitations(domain: str | None = None, status_value: str | None = Query(default=None, alias="status"), public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if domain: filters.append(KnownLimitation.domain == domain)
    if status_value: filters.append(KnownLimitation.status == status_value)
    if public is not None: filters.append(KnownLimitation.public.is_(public))
    return list(db.scalars(select(KnownLimitation).where(*filters).order_by(KnownLimitation.domain, KnownLimitation.title).limit(limit)).all())


@router.post("/limitations", response_model=KnownLimitationRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_limitation(payload: KnownLimitationCreate, db: Session = Depends(get_session)):
    return create_limitation(db, payload)


@router.get("/limitations/{limitation_id:path}", response_model=KnownLimitationRead, dependencies=[Depends(require_read)])
def limitation(limitation_id: str, db: Session = Depends(get_session)):
    return get_limitation_or_404(db, limitation_id)


@router.patch("/limitations/{limitation_id:path}", response_model=KnownLimitationRead, dependencies=[Depends(require_write)])
def patch_limitation(limitation_id: str, payload: KnownLimitationUpdate, db: Session = Depends(get_session)):
    return update_limitation(db, limitation_id, payload)


@router.get("/attestations", response_model=list[TrustAttestationRead], dependencies=[Depends(require_read)])
def attestations(status_value: str | None = Query(default=None, alias="status"), public: bool | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_session)):
    filters = []
    if status_value: filters.append(TrustAttestation.status == status_value)
    if public is not None: filters.append(TrustAttestation.public.is_(public))
    return list(db.scalars(select(TrustAttestation).where(*filters).order_by(TrustAttestation.valid_from.desc()).limit(limit)).all())


@router.post("/attestations", response_model=TrustAttestationRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_attestation(payload: TrustAttestationCreate, db: Session = Depends(get_session)):
    return create_attestation(db, payload)


@router.get("/attestations/{attestation_id:path}", response_model=TrustAttestationRead, dependencies=[Depends(require_read)])
def attestation(attestation_id: str, db: Session = Depends(get_session)):
    return get_attestation_or_404(db, attestation_id)


@router.post("/attestations/{attestation_id:path}/revoke", response_model=TrustAttestationRead, dependencies=[Depends(require_write)])
def post_revoke_attestation(attestation_id: str, payload: TrustAttestationRevoke, db: Session = Depends(get_session)):
    return revoke_attestation(db, attestation_id, payload.reason, payload.revoked_by)
