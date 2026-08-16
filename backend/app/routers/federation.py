from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..models import FederationExchangeManifest
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import federation
router=APIRouter(prefix="/v1/federation",tags=["Federated Core & Trusted Node Exchange"])
public_router=APIRouter(prefix="/api/v1/federation",tags=["Unified Public API — Federation Status"])
class NodeCreate(BaseModel):
    node_key:str=Field(min_length=1,max_length=255); name:str=Field(min_length=1,max_length=300); environment:str="production"; base_url:str|None=None; trust_state:str="pending"; signing_key_id:str|None=None; signing_key_fingerprint:str|None=None; capabilities:list=Field(default_factory=list); metadata:dict=Field(default_factory=dict)
class TrustCreate(BaseModel):
    relationship_key:str=Field(min_length=1,max_length=255); remote_node_key:str=Field(min_length=1,max_length=255); allowed_subject_types:list=Field(default_factory=list); allow_snapshots:bool=False; allow_private_records:bool=False; signature_required:bool=True; metadata:dict=Field(default_factory=dict)
class OutboundManifest(BaseModel):
    manifest_key:str=Field(min_length=1,max_length=255); target_node_key:str=Field(min_length=1,max_length=255); items:list=Field(min_length=1); metadata:dict=Field(default_factory=dict)
class InboundManifest(BaseModel):
    manifest_key:str=Field(min_length=1,max_length=255); origin_node_key:str=Field(min_length=1,max_length=255); manifest:dict; signature_value:str|None=None; signature_key_id:str|None=None; metadata:dict=Field(default_factory=dict)
class Accept(BaseModel): actor:str="operator"
def rowdict(row): return {c.key:getattr(row,c.key) for c in row.__table__.columns}
def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    s=federation.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); s.update({"release":request.app.state.settings.version,"migration_0026_applied":"0026" in m["applied"],"pending_migrations":m["pending"]}); return s
@router.post('/nodes',dependencies=[Depends(require_write)])
def node(payload:NodeCreate,db:Session=Depends(get_session)):
    try:return rowdict(federation.register_node(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/nodes',dependencies=[Depends(require_read)])
def nodes(db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in federation.list_nodes(db)]}
@router.post('/trust',dependencies=[Depends(require_write)])
def trust(payload:TrustCreate,db:Session=Depends(get_session)):
    try:return rowdict(federation.create_trust(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/trust',dependencies=[Depends(require_read)])
def trusts(db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in federation.list_trust(db)]}
@router.post('/manifests/outbound',dependencies=[Depends(require_write)])
def outbound(request:Request,payload:OutboundManifest,db:Session=Depends(get_session)):
    try:return rowdict(federation.create_outbound_manifest(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/manifests/inbound',dependencies=[Depends(require_write)])
def inbound(request:Request,payload:InboundManifest,db:Session=Depends(get_session)):
    try:return rowdict(federation.ingest_manifest(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/manifests/{manifest_id}/accept',dependencies=[Depends(require_write)])
def accept(manifest_id:str,payload:Accept,db:Session=Depends(get_session)):
    row=db.get(FederationExchangeManifest,manifest_id)
    if not row: raise HTTPException(status_code=404,detail="Manifest not found.")
    try:return rowdict(federation.accept_manifest(db,row,actor=payload.actor))
    except ValueError as e: raise bad(e)
@router.get('/manifests',dependencies=[Depends(require_read)])
def manifests(limit:int=100,db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in federation.list_manifests(db,max(1,min(limit,500)))]}
@router.get('/remote-references',dependencies=[Depends(require_read)])
def references(limit:int=200,db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in federation.list_references(db,max(1,min(limit,1000)))]}
@public_router.get('/status')
def public_status(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    if not request.app.state.settings.federation_public_status_enabled: raise HTTPException(status_code=404,detail="Public federation status is disabled.")
    return PublicEnvelope(data=federation.public_status(db,request.app.state.settings),meta={"api_version":"v1","request_id":request.state.request_id})
