from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import unified_research_runtime as svc
router=APIRouter(prefix="/v1/research/runtime-contract",tags=["research-runtime-contract"])
public_router=APIRouter(prefix="/api/v1/research/runtime-contract",tags=["public-research-runtime-contract"])
class Payload(BaseModel): data: dict
def enabled(request):
    if not request.app.state.settings.unified_research_runtime_contract_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try: return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/contracts",dependencies=[Depends(require_write)])
def contract(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_contract,db,payload.data)
@router.post("/object-types",dependencies=[Depends(require_write)])
def object_type(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_object_type,db,payload.data)
@router.post("/operations",dependencies=[Depends(require_write)])
def operation(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_operation,db,payload.data)
@router.post("/capabilities",dependencies=[Depends(require_write)])
def capability(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_capability,db,payload.data)
@router.post("/product-bindings",dependencies=[Depends(require_write)])
def product_binding(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bind_product,db,payload.data)
@router.post("/exchanges",dependencies=[Depends(require_write)])
def exchange(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_exchange,db,payload.data)
@router.post("/invocations",dependencies=[Depends(require_write)])
def invocation(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_invocation,db,payload.data)
@router.post("/results",dependencies=[Depends(require_write)])
def result(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bind_result,db,payload.data)
@router.post("/compatibility-assertions",dependencies=[Depends(require_write)])
def compatibility_assertion(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_compatibility,db,payload.data)
@router.get("/contracts/{contract_id}/products/{product_binding_id}/compatibility",dependencies=[Depends(require_read)])
def compatibility(contract_id:str,product_binding_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.compatibility_report,db,contract_id,product_binding_id)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revision(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/contracts/{contract_id}/bundle",dependencies=[Depends(require_read)])
def contract_bundle(contract_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.contract_bundle,db,contract_id)
@router.get("/projects/{project_ref:path}/bundle",dependencies=[Depends(require_read)])
def project_bundle(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.project_bundle,db,project_ref)
@public_router.get("/contracts/{contract_id}/bundle",response_model=PublicEnvelope)
def public_contract_bundle(contract_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.contract_bundle,db,contract_id,True),meta={"release":"2.96.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/bundle",response_model=PublicEnvelope)
def public_project_bundle(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.project_bundle,db,project_ref,True),meta={"release":"2.96.0","contract":svc.CONTRACT})
