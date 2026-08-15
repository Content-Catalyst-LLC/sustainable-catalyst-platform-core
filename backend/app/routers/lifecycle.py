
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..models import PreservationArchiveRecord,LifecycleHoldRecord
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import lifecycle
router=APIRouter(prefix="/v1/lifecycle",tags=["Data Lifecycle, Archival Integrity & Preservation"])
public_router=APIRouter(prefix="/api/v1/lifecycle",tags=["Unified Public API — Preservation Status"])
class PolicyCreate(BaseModel):
    policy_key:str=Field(min_length=1,max_length=255); subject_type:str="evidence-record"; retention_class:str="institutional"; minimum_retention_days:int|None=None; archive_after_days:int|None=None; tombstone_after_days:int|None=None; preserve_provenance:bool=True; hold_overrides_lifecycle:bool=True; metadata:dict=Field(default_factory=dict)
class ArchiveCreate(BaseModel):
    archive_key:str=Field(min_length=1,max_length=255); subject_type:str; subject_id:str; snapshot:dict=Field(default_factory=dict); storage_kind:str="core-manifest"; storage_uri:str|None=None; metadata:dict=Field(default_factory=dict)
class HoldCreate(BaseModel):
    hold_key:str=Field(min_length=1,max_length=255); subject_type:str; subject_id:str; hold_type:str="policy"; reason:str=""; actor:str="operator"; metadata:dict=Field(default_factory=dict)
class Actor(BaseModel): actor:str="operator"
class Tombstone(BaseModel): subject_type:str; subject_id:str; actor:str="operator"; reason:str="retention-policy"
class Restore(BaseModel): actor:str="operator"; reason:str="operator-request"
def rowdict(row): return {c.key:getattr(row,c.key) for c in row.__table__.columns}
def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    s=lifecycle.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); s.update({"release":request.app.state.settings.version,"migration_0025_applied":"0025" in m["applied"],"pending_migrations":m["pending"]}); return s
@router.post('/policies',dependencies=[Depends(require_write)])
def create_policy(request:Request,payload:PolicyCreate,db:Session=Depends(get_session)):
    try:return rowdict(lifecycle.create_policy(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/policies',dependencies=[Depends(require_read)])
def policies(db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in lifecycle.list_policies(db)]}
@router.post('/archives',dependencies=[Depends(require_write)])
def archive(payload:ArchiveCreate,db:Session=Depends(get_session)):
    try:return rowdict(lifecycle.create_archive(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/archives/{archive_id}/verify',dependencies=[Depends(require_write)])
def verify(archive_id:str,db:Session=Depends(get_session)):
    row=db.get(PreservationArchiveRecord,archive_id)
    if not row: raise HTTPException(status_code=404,detail="Archive not found.")
    return lifecycle.verify_archive(db,row)
@router.post('/archives/{archive_id}/restore',dependencies=[Depends(require_write)])
def restore(archive_id:str,payload:Restore,db:Session=Depends(get_session)):
    row=db.get(PreservationArchiveRecord,archive_id)
    if not row: raise HTTPException(status_code=404,detail="Archive not found.")
    try:return rowdict(lifecycle.restore_archive(db,row,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/holds',dependencies=[Depends(require_write)])
def hold(payload:HoldCreate,db:Session=Depends(get_session)):
    try:return rowdict(lifecycle.place_hold(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/holds/{hold_id}/release',dependencies=[Depends(require_write)])
def release_hold(hold_id:str,payload:Actor,db:Session=Depends(get_session)):
    row=db.get(LifecycleHoldRecord,hold_id)
    if not row: raise HTTPException(status_code=404,detail="Hold not found.")
    return rowdict(lifecycle.release_hold(db,row,actor=payload.actor))
@router.post('/tombstones',dependencies=[Depends(require_write)])
def tombstone(payload:Tombstone,db:Session=Depends(get_session)): return rowdict(lifecycle.request_tombstone(db,**payload.model_dump()))
@public_router.get('/status')
def public_status(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    if not request.app.state.settings.data_lifecycle_public_status_enabled: raise HTTPException(status_code=404,detail="Public preservation status is disabled.")
    return PublicEnvelope(data=lifecycle.public_status(db,request.app.state.settings),meta={"api_version":"v1","request_id":request.state.request_id})
