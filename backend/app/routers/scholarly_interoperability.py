from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import scholarly_interoperability as svc
router=APIRouter(prefix="/v1/research/scholarly-packages",tags=["research-scholarly-packages"])
public_router=APIRouter(prefix="/api/v1/research/scholarly-packages",tags=["public-research-scholarly-packages"])
class Payload(BaseModel): data: dict
def enabled(request):
 if not request.app.state.settings.scholarly_interoperability_research_packaging_enabled: raise HTTPException(404,"feature disabled")
def call(fn,*a):
 try: return fn(*a)
 except ValueError as e: raise HTTPException(400,str(e)) from e
@router.get("/readiness",dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)): enabled(request); return svc.readiness(db)
for path,name in []: pass
@router.post("/packages",dependencies=[Depends(require_write)])
def package(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.create_package,db,payload.data)
@router.post("/members",dependencies=[Depends(require_write)])
def member(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_member,db,payload.data)
@router.post("/citations",dependencies=[Depends(require_write)])
def citation(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_citation,db,payload.data)
@router.post("/identifiers",dependencies=[Depends(require_write)])
def identifier(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_identifier,db,payload.data)
@router.post("/datasets",dependencies=[Depends(require_write)])
def dataset(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_dataset,db,payload.data)
@router.post("/notebooks",dependencies=[Depends(require_write)])
def notebook(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_notebook,db,payload.data)
@router.post("/provenance-manifests",dependencies=[Depends(require_write)])
def manifest(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_manifest,db,payload.data)
@router.post("/metadata-profiles",dependencies=[Depends(require_write)])
def metadata_profile(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_metadata_profile,db,payload.data)
@router.post("/export-profiles",dependencies=[Depends(require_write)])
def export_profile(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.add_export_profile,db,payload.data)
@router.post("/publication-bindings",dependencies=[Depends(require_write)])
def pub_binding(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bind_publication_object,db,payload.data)
@router.post("/validations",dependencies=[Depends(require_write)])
def validation(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.record_validation,db,payload.data)
@router.post("/revisions",dependencies=[Depends(require_write)])
def revision(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.revise,db,payload.data)
@router.post("/snapshots",dependencies=[Depends(require_write)])
def snapshot(payload:Payload,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.snapshot,db,payload.data)
@router.get("/projects/{project_ref:path}/summary",dependencies=[Depends(require_read)])
def summary(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.summary,db,project_ref)
@router.get("/projects/{project_ref:path}/lineage",dependencies=[Depends(require_read)])
def lineage(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.lineage,db,project_ref)
@router.get("/projects/{project_ref:path}/bundle",dependencies=[Depends(require_read)])
def bundle(project_ref:str,request:Request,db:Session=Depends(get_session)): enabled(request); return call(svc.bundle,db,project_ref)
@public_router.get("/projects/{project_ref:path}/summary",response_model=PublicEnvelope)
def public_summary(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.summary,db,project_ref,True),meta={"release":"2.95.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/lineage",response_model=PublicEnvelope)
def public_lineage(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.lineage,db,project_ref,True),meta={"release":"2.95.0","contract":svc.CONTRACT})
@public_router.get("/projects/{project_ref:path}/bundle",response_model=PublicEnvelope)
def public_bundle(project_ref:str,request:Request,db:Session=Depends(get_session),ctx:PublicApiContext=Depends(require_public_scope("data:read"))): enabled(request); return PublicEnvelope(data=call(svc.bundle,db,project_ref,True),meta={"release":"2.95.0","contract":svc.CONTRACT})
