from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_portfolios as svc
router=APIRouter(prefix="/v1/research/portfolios",tags=["Research Portfolio & Institutional Knowledge Governance"])
public_router=APIRouter(prefix="/api/v1/research/portfolios",tags=["Unified Public API — Research Portfolio & Institutional Knowledge Governance"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
    if not request.app.state.settings.research_portfolio_institutional_governance_enabled: raise HTTPException(503,"Research Portfolio & Institutional Knowledge Governance is disabled.")
def call(fn,*args):
    try:return fn(*args)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0089_applied"]="0089" in migration_status(request.app.state.database)["applied"]; return out
@router.post("",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_portfolio,db,payload.data)
@router.post("/{portfolio_id}/programs",dependencies=[Depends(require_write)])
def add_program(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_program,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/themes",dependencies=[Depends(require_write)])
def add_theme(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_theme,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/objectives",dependencies=[Depends(require_write)])
def add_objective(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_objective,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/dependencies",dependencies=[Depends(require_write)])
def add_dependency(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_dependency,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/resources",dependencies=[Depends(require_write)])
def add_resource(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_resource_envelope,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/risks",dependencies=[Depends(require_write)])
def add_risk(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_risk,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/reviews",dependencies=[Depends(require_write)])
def add_review(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_review,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/decisions",dependencies=[Depends(require_write)])
def add_decision(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_decision,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/revisions",dependencies=[Depends(require_write)])
def revise(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_portfolio,db,portfolio_id,payload.data)
@router.post("/{portfolio_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(portfolio_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,portfolio_id,payload.data)
@router.get("/{portfolio_id}/summary",dependencies=[Depends(require_read)])
def summary(portfolio_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,portfolio_id)
@router.get("/{portfolio_id}/map",dependencies=[Depends(require_read)])
def pmap(portfolio_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.portfolio_map,db,portfolio_id)
@router.get("/{portfolio_id}/lineage",dependencies=[Depends(require_read)])
def lineage(portfolio_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,portfolio_id)
@router.get("/{portfolio_id}/bundle",dependencies=[Depends(require_read)])
def bundle(portfolio_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,portfolio_id)
@public_router.get("/{portfolio_id}/summary",response_model=PublicEnvelope)
def public_summary(portfolio_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,portfolio_id,True),meta={"release":"2.85.0","contract":svc.CONTRACT})
@public_router.get("/{portfolio_id}/map",response_model=PublicEnvelope)
def public_map(portfolio_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.portfolio_map,db,portfolio_id,True),meta={"release":"2.85.0","contract":svc.CONTRACT})
@public_router.get("/{portfolio_id}/lineage",response_model=PublicEnvelope)
def public_lineage(portfolio_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,portfolio_id,True),meta={"release":"2.85.0","contract":svc.CONTRACT})
@public_router.get("/{portfolio_id}/bundle",response_model=PublicEnvelope)
def public_bundle(portfolio_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,portfolio_id,True),meta={"release":"2.85.0","contract":svc.CONTRACT})
