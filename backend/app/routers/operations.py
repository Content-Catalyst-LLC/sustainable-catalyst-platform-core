from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..models import ChangeControlRecord, OperationsIncident, RollbackCoordinationRecord
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import operations

router=APIRouter(prefix="/v1/operations",tags=["Incident Response, Change Control & Rollback Coordination"])
public_router=APIRouter(prefix="/api/v1/operations",tags=["Unified Public API — Operational Status"])

class IncidentCreate(BaseModel):
    title:str=Field(min_length=1,max_length=300); service:str="platform-core"; environment:str="production"; severity:str="sev3"; source:str="manual"; source_ref:str|None=None; summary:str|None=None; owner:str="unassigned"; visibility:str="internal"; idempotency_key:str|None=None; metadata:dict=Field(default_factory=dict)
class IncidentTransition(BaseModel):
    state:str; actor:str="operator"; note:str|None=None; details:dict=Field(default_factory=dict)
class ChangeCreate(BaseModel):
    change_key:str=Field(min_length=1,max_length=255); service:str="platform-core"; release:str|None=None; environment:str="production"; change_type:str="deployment"; risk:str="medium"; actor:str="operator"; incident_id:str|None=None; deployment_marker_id:str|None=None; details:dict=Field(default_factory=dict)
class ActorAction(BaseModel): actor:str="operator"; note:str|None=None; details:dict=Field(default_factory=dict)
class RollbackAssessment(BaseModel): deployment_marker_id:str|None=None; slo_evaluations:list[dict]=Field(default_factory=list)
class RollbackDecision(BaseModel): state:str; actor:str="operator"; note:str|None=None

def rowdict(row): return {c.key:getattr(row,c.key) for c in row.__table__.columns}
def bad(exc): return HTTPException(status_code=422,detail=str(exc))

def get_incident(db,id):
    row=db.get(OperationsIncident,id)
    if not row: raise HTTPException(status_code=404,detail="Incident not found.")
    return row

def get_change(db,id):
    row=db.get(ChangeControlRecord,id)
    if not row: raise HTTPException(status_code=404,detail="Change not found.")
    return row

def get_rollback(db,id):
    row=db.get(RollbackCoordinationRecord,id)
    if not row: raise HTTPException(status_code=404,detail="Rollback coordination record not found.")
    return row

@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    d=operations.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); d.update({"release":request.app.state.settings.version,"migration_0022_applied":"0022" in m["applied"],"pending_migrations":m["pending"],"status":"ready" if d["enabled"] else "disabled"}); return d

@router.post("/incidents",dependencies=[Depends(require_write)])
def create_incident(payload:IncidentCreate,db:Session=Depends(get_session)):
    try: return rowdict(operations.create_incident(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)

@router.get("/incidents",dependencies=[Depends(require_read)])
def list_incidents(state:str|None=None,service:str|None=None,limit:int=Query(default=100,ge=1,le=500),db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in operations.list_incidents(db,state=state,service=service,limit=limit)]}

@router.post("/incidents/{incident_id}/transition",dependencies=[Depends(require_write)])
def transition(incident_id:str,payload:IncidentTransition,db:Session=Depends(get_session)):
    row=get_incident(db,incident_id)
    try: operations.append_event(db,row,event_type="incident.state_changed",actor=payload.actor,new_state=payload.state,note=payload.note,details=payload.details); return rowdict(row)
    except ValueError as e: raise bad(e)

@router.get("/incidents/{incident_id}/events",dependencies=[Depends(require_read)])
def incident_events(incident_id:str,db:Session=Depends(get_session)): get_incident(db,incident_id); return {"items":[rowdict(x) for x in operations.events(db,incident_id)]}

@router.get("/incidents/{incident_id}/events/verify",dependencies=[Depends(require_read)])
def verify_events(incident_id:str,db:Session=Depends(get_session)): get_incident(db,incident_id); return operations.verify_event_chain(db,incident_id)

@router.post("/changes",dependencies=[Depends(require_write)])
def create_change(request:Request,payload:ChangeCreate,db:Session=Depends(get_session)):
    try: return rowdict(operations.create_change(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)

@router.post("/changes/{change_id}/approve",dependencies=[Depends(require_write)])
def approve(change_id:str,payload:ActorAction,db:Session=Depends(get_session)):
    try: return rowdict(operations.approve_change(db,get_change(db,change_id),actor=payload.actor))
    except ValueError as e: raise bad(e)

@router.post("/changes/{change_id}/start",dependencies=[Depends(require_write)])
def start(change_id:str,payload:ActorAction,db:Session=Depends(get_session)):
    try: return rowdict(operations.start_change(db,get_change(db,change_id),actor=payload.actor))
    except ValueError as e: raise bad(e)

@router.post("/changes/{change_id}/finish",dependencies=[Depends(require_write)])
def finish(change_id:str,state:str,payload:ActorAction,db:Session=Depends(get_session)):
    try: return rowdict(operations.finish_change(db,get_change(db,change_id),state=state,actor=payload.actor,details=payload.details))
    except ValueError as e: raise bad(e)

@router.post("/incidents/{incident_id}/rollback-assessment",dependencies=[Depends(require_write)])
def rollback_assessment(incident_id:str,payload:RollbackAssessment,db:Session=Depends(get_session)):
    try: return rowdict(operations.assess_rollback(db,incident=get_incident(db,incident_id),deployment_marker_id=payload.deployment_marker_id,slo_evaluations=payload.slo_evaluations))
    except ValueError as e: raise bad(e)

@router.post("/rollback/{rollback_id}/decision",dependencies=[Depends(require_write)])
def rollback_decision(rollback_id:str,payload:RollbackDecision,db:Session=Depends(get_session)):
    try: return rowdict(operations.decide_rollback(db,get_rollback(db,rollback_id),state=payload.state,actor=payload.actor,note=payload.note))
    except ValueError as e: raise bad(e)

@public_router.get("/status")
def status(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope("data:read"))):
    settings=request.app.state.settings
    if not settings.incident_public_status_enabled: raise HTTPException(status_code=404,detail="Public operational status is disabled.")
    return PublicEnvelope(data=operations.public_status(db,settings),meta={"api_version":"v1","request_id":request.state.request_id})
