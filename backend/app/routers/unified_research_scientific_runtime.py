from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import unified_research_scientific_runtime as svc
router=APIRouter(prefix="/v1/research/unified-runtime",tags=["unified-research-runtime-v3"])
public_router=APIRouter(prefix="/api/v1/research/unified-runtime",tags=["public-unified-research-runtime-v3"])
class Payload(BaseModel): data:dict
def enabled(request):
 if not request.app.state.settings.unified_research_scientific_investigation_runtime_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
 try:return fn(*a)
 except ValueError as e: raise HTTPException(400,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/sessions",dependencies=[Depends(require_write)])
def session(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_session,db,payload.data)
@router.post("/object-bindings",dependencies=[Depends(require_write)])
def add_object_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_object_binding,db,payload.data)
@router.post("/product-bindings",dependencies=[Depends(require_write)])
def add_product_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_product_binding,db,payload.data)
@router.post("/execution-bindings",dependencies=[Depends(require_write)])
def add_execution_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_execution_binding,db,payload.data)
@router.post("/investigation-bindings",dependencies=[Depends(require_write)])
def add_investigation_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_investigation_binding,db,payload.data)
@router.post("/visual-bindings",dependencies=[Depends(require_write)])
def add_visual_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_visual_binding,db,payload.data)
@router.post("/validation-bindings",dependencies=[Depends(require_write)])
def add_validation_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_validation_binding,db,payload.data)
@router.post("/package-bindings",dependencies=[Depends(require_write)])
def add_package_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_package_binding,db,payload.data)
@router.post("/handoff-bindings",dependencies=[Depends(require_write)])
def add_handoff_binding_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_handoff_binding,db,payload.data)
@router.post("/milestones",dependencies=[Depends(require_write)])
def add_milestone_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_milestone,db,payload.data)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revise_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot_route(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/sessions/{session_id}/summary",dependencies=[Depends(require_read)])
def summary(session_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.summary,db,session_id)
@router.get("/sessions/{session_id}/lineage",dependencies=[Depends(require_read)])
def lineage(session_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,session_id)
@router.get("/sessions/{session_id}/bundle",dependencies=[Depends(require_read)])
def bundle(session_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,session_id)
@public_router.get("/sessions/{session_id}/summary",response_model=PublicEnvelope)
def public_summary(session_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.summary,db,session_id,True),meta={"release":"3.0.0","contract":svc.CONTRACT})
@public_router.get("/sessions/{session_id}/lineage",response_model=PublicEnvelope)
def public_lineage(session_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,session_id,True),meta={"release":"3.0.0","contract":svc.CONTRACT})
@public_router.get("/sessions/{session_id}/bundle",response_model=PublicEnvelope)
def public_bundle(session_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,session_id,True),meta={"release":"3.0.0","contract":svc.CONTRACT})
