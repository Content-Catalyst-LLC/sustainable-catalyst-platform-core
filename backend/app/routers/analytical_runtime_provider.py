from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import analytical_runtime_provider as svc

router=APIRouter(prefix="/v1/analytics/runtime-providers",tags=["analytical-runtime-provider-v310"])
public_router=APIRouter(prefix="/api/v1/analytics/runtime-providers",tags=["public-analytical-runtime-provider-v310"])
class Payload(BaseModel): data:dict
def enabled(request):
    if not request.app.state.settings.analytical_runtime_provider_contract_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try:return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e

@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.get("/providers",dependencies=[Depends(require_read)])
def providers(request:Request,db:Session=Depends(get_session)): enabled(request); return {"release":svc.RELEASE,"providers":svc.list_providers(db)}
@router.get("/providers/{provider_ref}",dependencies=[Depends(require_read)])
def provider(provider_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.provider_bundle,db,provider_ref)
@router.post("/providers",dependencies=[Depends(require_write)])
def register_provider(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.register_provider,db,payload.data)
@router.post("/capabilities",dependencies=[Depends(require_write)])
def capability(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.register_capability,db,payload.data)
@router.post("/requests",dependencies=[Depends(require_write)])
def create_request(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_request,db,payload.data)
@router.post("/environments",dependencies=[Depends(require_write)])
def environment(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_environment,db,payload.data)
@router.post("/results",dependencies=[Depends(require_write)])
def result(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_result,db,payload.data)
@router.post("/artifacts",dependencies=[Depends(require_write)])
def artifact(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_artifact,db,payload.data)
@router.post("/diagnostics",dependencies=[Depends(require_write)])
def diagnostic(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_diagnostic,db,payload.data)
@router.post("/reproductions",dependencies=[Depends(require_write)])
def reproduction(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_reproduction,db,payload.data)
@router.get("/requests/{request_ref}/bundle",dependencies=[Depends(require_read)])
def bundle(request_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.request_bundle,db,request_ref)

@public_router.get("/readiness",response_model=PublicEnvelope)
def public_readiness(request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=svc.readiness(db),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
@public_router.get("/providers",response_model=PublicEnvelope)
def public_providers(request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=svc.list_providers(db,True),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
@public_router.get("/providers/{provider_ref}",response_model=PublicEnvelope)
def public_provider(provider_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.provider_bundle,db,provider_ref,True),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
@public_router.get("/requests/{request_ref}/bundle",response_model=PublicEnvelope)
def public_bundle(request_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.request_bundle,db,request_ref,True),meta={"release":svc.RELEASE,"contract":svc.CONTRACT})
