from typing import Any
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import research_context_handoffs as svc
router=APIRouter(prefix="/v1/research/context-handoffs",tags=["Cross-Product Research Context & Handoff Protocol"])
public_router=APIRouter(prefix="/api/v1/research/context-handoffs",tags=["Unified Public API — Research Context Handoffs"])
class Payload(BaseModel): data:dict[str,Any]=Field(default_factory=dict)
def enabled(request:Request):
 if not request.app.state.settings.cross_product_research_context_handoff_enabled: raise HTTPException(503,"Cross-Product Research Context & Handoff Protocol is disabled.")
def call(fn,*args):
 try:return fn(*args)
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/readiness",dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)): enabled(request); out=svc.readiness(db); out["migration_0095_applied"]="0095" in migration_status(request.app.state.database)["applied"]; return out
@router.post("/contexts",dependencies=[Depends(require_write)])
def create(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_context,db,payload.data)
@router.post("/contexts/{context_id}/object-bindings",dependencies=[Depends(require_write)])
def object_binding(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_object_binding,db,context_id,payload.data)
@router.post("/contexts/{context_id}/provenance-bindings",dependencies=[Depends(require_write)])
def provenance_binding(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_provenance_binding,db,context_id,payload.data)
@router.post("/contexts/{context_id}/state-markers",dependencies=[Depends(require_write)])
def state_marker(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_state_marker,db,context_id,payload.data)
@router.post("/contexts/{context_id}/protocols",dependencies=[Depends(require_write)])
def protocol(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_protocol,db,context_id,payload.data)
@router.get("/contexts/{context_id}/protocols/{handoff_key}/diagnostics",dependencies=[Depends(require_read)])
def diagnostics(context_id:str,handoff_key:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.contract_diagnostics,db,context_id,handoff_key)
@router.post("/contexts/{context_id}/packages",dependencies=[Depends(require_write)])
def package(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_package,db,context_id,payload.data)
@router.post("/contexts/{context_id}/packages/{package_key}/acknowledgements",dependencies=[Depends(require_write)])
def acknowledge(context_id:str,package_key:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.acknowledge_package,db,context_id,package_key,payload.data)
@router.post("/contexts/{context_id}/conflicts",dependencies=[Depends(require_write)])
def conflict(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_conflict,db,context_id,payload.data)
@router.post("/contexts/{context_id}/revisions",dependencies=[Depends(require_write)])
def revise(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise_context,db,context_id,payload.data)
@router.post("/contexts/{context_id}/snapshots",dependencies=[Depends(require_write)])
def snapshot(context_id:str,payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,context_id,payload.data)
@router.get("/contexts/{context_id}/summary",dependencies=[Depends(require_read)])
def summary(context_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.descriptive_summary,db,context_id)
@router.get("/contexts/{context_id}/lineage",dependencies=[Depends(require_read)])
def lineage(context_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,context_id)
@router.get("/contexts/{context_id}/bundle",dependencies=[Depends(require_read)])
def bundle(context_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,context_id)
@public_router.get("/contexts/{context_id}/summary",response_model=PublicEnvelope)
def public_summary(context_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.descriptive_summary,db,context_id,True),meta={"release":"2.91.0","contract":svc.CONTRACT})
@public_router.get("/contexts/{context_id}/lineage",response_model=PublicEnvelope)
def public_lineage(context_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,context_id,True),meta={"release":"2.91.0","contract":svc.CONTRACT})
@public_router.get("/contexts/{context_id}/bundle",response_model=PublicEnvelope)
def public_bundle(context_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,context_id,True),meta={"release":"2.91.0","contract":svc.CONTRACT})
