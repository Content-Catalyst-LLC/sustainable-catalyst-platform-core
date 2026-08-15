from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services.governance import (
    bind_role, create_policy, create_retention_policy, evaluate_access, list_audit_events,
    list_decisions, list_policies, list_roles, readiness, verify_audit_chain,
)

router = APIRouter(prefix="/v1/governance", tags=["Governance, Access & Audit"])
public_router = APIRouter(prefix="/api/v1/governance", tags=["Unified Public API — Governance Readiness"])

class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    effect: str
    principal_type: str = "any"
    principal_id: str | None = None
    product_scope: str | None = None
    resource_type: str = "*"
    action: str = "*"
    visibility_ceiling: str = "internal"
    priority: int = Field(default=100, ge=0, le=100000)
    enabled: bool = True
    conditions: dict = Field(default_factory=dict)
    description: str | None = None
    created_by: str = "operator"

class RoleCreate(BaseModel):
    principal_type: str
    principal_id: str
    role: str
    product_scope: str | None = None
    metadata: dict = Field(default_factory=dict)
    active: bool = True

class DecisionEvaluate(BaseModel):
    principal_type: str
    principal_id: str
    product: str | None = None
    resource_type: str
    resource_id: str | None = None
    action: str
    requested_visibility: str = "internal"
    request_id: str | None = None
    context: dict = Field(default_factory=dict)

class RetentionCreate(BaseModel):
    resource_type: str
    retention_hours: int = Field(ge=24)
    disposition: str = "compact"
    metadata: dict = Field(default_factory=dict)

def _bad(exc: ValueError): return HTTPException(status_code=422, detail=str(exc))

def _row(row):
    return {c.key: getattr(row, c.key) for c in row.__table__.columns}

@router.get("/readiness", dependencies=[Depends(require_read)])
def governance_readiness(request: Request):
    status=migration_status(request.app.state.database); data=readiness(request.app.state.settings)
    data.update({"status": "ready" if data["enabled"] else "disabled", "release": request.app.state.settings.version,
                 "migration_0019_applied": "0019" in status["applied"], "pending_migrations": status["pending"]})
    return data

@router.post("/policies", dependencies=[Depends(require_write)])
def policy_create(payload: PolicyCreate, db: Session=Depends(get_session)):
    try: return jsonable_encoder(_row(create_policy(db, **payload.model_dump())))
    except ValueError as exc: raise _bad(exc)

@router.get("/policies", dependencies=[Depends(require_write)])
def policies(limit: int=Query(200,ge=1,le=1000), db: Session=Depends(get_session)):
    return {"items": jsonable_encoder([_row(x) for x in list_policies(db,limit)])}

@router.post("/roles", dependencies=[Depends(require_write)])
def role_create(payload: RoleCreate, db: Session=Depends(get_session)):
    try: return jsonable_encoder(_row(bind_role(db, **payload.model_dump())))
    except ValueError as exc: raise _bad(exc)

@router.get("/roles", dependencies=[Depends(require_write)])
def roles(limit: int=Query(200,ge=1,le=1000), db: Session=Depends(get_session)):
    return {"items": jsonable_encoder([_row(x) for x in list_roles(db,limit)])}

@router.post("/decisions/evaluate", dependencies=[Depends(require_write)])
def decision_evaluate(payload: DecisionEvaluate, request: Request, db: Session=Depends(get_session)):
    try:
        data=payload.model_dump(); data["request_id"] = data.get("request_id") or getattr(request.state,"request_id",None)
        return evaluate_access(db, request.app.state.settings, **data)
    except ValueError as exc: raise _bad(exc)

@router.get("/decisions", dependencies=[Depends(require_write)])
def decisions(limit: int=Query(200,ge=1,le=1000), db: Session=Depends(get_session)):
    return {"items": jsonable_encoder([_row(x) for x in list_decisions(db,limit)])}

@router.get("/audit", dependencies=[Depends(require_write)])
def audit(limit: int=Query(200,ge=1,le=1000), db: Session=Depends(get_session)):
    return {"items": jsonable_encoder([_row(x) for x in list_audit_events(db,limit)])}

@router.get("/audit/verify", dependencies=[Depends(require_write)])
def audit_verify(db: Session=Depends(get_session)):
    return verify_audit_chain(db)

@router.post("/retention-policies", dependencies=[Depends(require_write)])
def retention_create(payload: RetentionCreate, db: Session=Depends(get_session)):
    try: return jsonable_encoder(_row(create_retention_policy(db, **payload.model_dump())))
    except ValueError as exc: raise _bad(exc)

@public_router.get("/readiness")
def public_governance_readiness(request: Request, _context: PublicApiContext=Depends(require_public_scope("data:read"))):
    data=readiness(request.app.state.settings)
    return PublicEnvelope(data=jsonable_encoder({"status":"ready" if data["enabled"] else "disabled","release":request.app.state.settings.version,
        "enforcement_mode":data["enforcement_mode"],"audit_chain":data["audit_chain"],"default_private_access":data["default_private_access"],
        "secret_values_persisted_in_audit":False,"policy_data_publicly_exposed":False,"audit_data_publicly_exposed":False}),
        meta={"api_version":"v1","request_id":request.state.request_id,"documentation":"/docs#tag/Unified-Public-API-Governance-Readiness"})
