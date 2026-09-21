from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import platform_research_certification as svc
router=APIRouter(prefix="/v1/research/integration-certification",tags=["research-integration-certification"])
public_router=APIRouter(prefix="/api/v1/research/integration-certification",tags=["public-research-integration-certification"])
class Payload(BaseModel): data: dict
def enabled(request):
    if not request.app.state.settings.platform_research_integration_certification_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
    try: return fn(*a)
    except ValueError as e: raise HTTPException(400,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
@router.post("/suites",dependencies=[Depends(require_write)])
def suite(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_suite,db,payload.data)
@router.post("/products",dependencies=[Depends(require_write)])
def product(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_product,db,payload.data)
@router.post("/cases",dependencies=[Depends(require_write)])
def case(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_case,db,payload.data)
@router.post("/runs",dependencies=[Depends(require_write)])
def run(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_run,db,payload.data)
@router.post("/case-results",dependencies=[Depends(require_write)])
def result(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_case_result,db,payload.data)
@router.post("/exchange-checks",dependencies=[Depends(require_write)])
def exchange(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_exchange_check,db,payload.data)
@router.post("/trace-checks",dependencies=[Depends(require_write)])
def trace(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_trace_check,db,payload.data)
@router.post("/reproduction-checks",dependencies=[Depends(require_write)])
def reproduce(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_reproduction_check,db,payload.data)
@router.post("/evidence",dependencies=[Depends(require_write)])
def evidence(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_evidence,db,payload.data)
@router.post("/findings",dependencies=[Depends(require_write)])
def finding(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_finding,db,payload.data)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revision(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/runs/{run_id}/report",dependencies=[Depends(require_read)])
def report(run_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.run_report,db,run_id)
@router.get("/suites/{suite_id}/bundle",dependencies=[Depends(require_read)])
def bundle(suite_id:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.suite_bundle,db,suite_id)
@public_router.get("/runs/{run_id}/report",response_model=PublicEnvelope)
def public_report(run_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.run_report,db,run_id,True),meta={"release":"2.97.0","contract":svc.CONTRACT})
@public_router.get("/suites/{suite_id}/bundle",response_model=PublicEnvelope)
def public_bundle(suite_id:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.suite_bundle,db,suite_id,True),meta={"release":"2.97.0","contract":svc.CONTRACT})
