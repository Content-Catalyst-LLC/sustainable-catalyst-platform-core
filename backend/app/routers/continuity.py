from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..models import BackupArtifactRecord
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import continuity
router=APIRouter(prefix="/v1/continuity",tags=["Continuity, Backup Verification & Disaster Recovery"])
public_router=APIRouter(prefix="/api/v1/continuity",tags=["Unified Public API — Continuity Status"])
class BackupCreate(BaseModel):
    backup_key:str=Field(min_length=1,max_length=255); environment:str="production"; database_engine:str="postgresql"; storage_kind:str="operator-managed"; storage_uri:str=Field(min_length=1,max_length=2000); checksum_sha256:str|None=None; size_bytes:int|None=None; backup_started_at:datetime|None=None; backup_completed_at:datetime|None=None; metadata:dict=Field(default_factory=dict)
class BackupAttestation(BaseModel):
    actor:str="operator"; observed_checksum_sha256:str; observed_size_bytes:int|None=None; evidence:dict=Field(default_factory=dict)
class ObjectiveUpsert(BaseModel):
    environment:str="production"; rpo_minutes:int=1440; rto_minutes:int=240; max_backup_age_minutes:int=1440; restore_rehearsal_max_age_hours:int=720; require_verified_backup:bool=True; require_restore_rehearsal:bool=True; metadata:dict=Field(default_factory=dict)
class ExternalRehearsal(BaseModel):
    state:str; operator_actor:str="operator"; schema_head:str|None=None; duration_ms:int; integrity_checks:dict=Field(default_factory=dict); evidence:dict=Field(default_factory=dict); environment:str|None=None

def rowdict(row,include_uri=False):
    data={c.key:getattr(row,c.key) for c in row.__table__.columns}
    if not include_uri: data.pop("storage_uri",None)
    return data

def get_backup(db,id):
    row=db.get(BackupArtifactRecord,id)
    if not row: raise HTTPException(status_code=404,detail="Backup artifact not found.")
    return row

def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,environment:str='production',db:Session=Depends(get_session)):
    s=continuity.continuity_status(db,request.app.state.settings,environment); m=migration_status(request.app.state.database); s.update({"release":request.app.state.settings.version,"migration_0023_applied":"0023" in m["applied"],"pending_migrations":m["pending"]}); return s
@router.post('/backups',dependencies=[Depends(require_write)])
def register(payload:BackupCreate,db:Session=Depends(get_session)):
    try:return rowdict(continuity.register_backup(db,**payload.model_dump()),include_uri=True)
    except ValueError as e: raise bad(e)
@router.get('/backups',dependencies=[Depends(require_read)])
def backups(environment:str|None=None,limit:int=Query(100,ge=1,le=500),db:Session=Depends(get_session)): return {"items":[rowdict(x,include_uri=True) for x in continuity.list_backups(db,environment,limit)]}
@router.post('/backups/{backup_id}/verify',dependencies=[Depends(require_write)])
def verify(backup_id:str,request:Request,db:Session=Depends(get_session)):
    try:return rowdict(continuity.verify_backup(db,get_backup(db,backup_id),request.app.state.settings),include_uri=True)
    except ValueError as e: raise bad(e)
@router.post('/backups/{backup_id}/attest-verification',dependencies=[Depends(require_write)])
def attest(backup_id:str,payload:BackupAttestation,db:Session=Depends(get_session)):
    try:return rowdict(continuity.attest_backup_verification(db,get_backup(db,backup_id),**payload.model_dump()),include_uri=True)
    except ValueError as e: raise bad(e)
@router.post('/objectives',dependencies=[Depends(require_write)])
def objective(request:Request,payload:ObjectiveUpsert,db:Session=Depends(get_session)):
    try:return rowdict(continuity.upsert_objective(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.post('/backups/{backup_id}/restore-rehearsals/sqlite',dependencies=[Depends(require_write)])
def sqlite_rehearsal(backup_id:str,request:Request,actor:str='operator',environment:str|None=None,db:Session=Depends(get_session)):
    try:return rowdict(continuity.run_sqlite_restore_rehearsal(db,get_backup(db,backup_id),request.app.state.settings,environment=environment,actor=actor))
    except ValueError as e: raise bad(e)
@router.post('/backups/{backup_id}/restore-rehearsals/external',dependencies=[Depends(require_write)])
def external_rehearsal(backup_id:str,payload:ExternalRehearsal,db:Session=Depends(get_session)):
    try:return rowdict(continuity.record_external_restore_rehearsal(db,get_backup(db,backup_id),**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/restore-rehearsals',dependencies=[Depends(require_read)])
def rehearsals(environment:str|None=None,limit:int=Query(100,ge=1,le=500),db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in continuity.list_rehearsals(db,environment,limit)]}
@public_router.get('/status')
def public_status(request:Request,environment:str='production',db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    if not request.app.state.settings.continuity_public_status_enabled: raise HTTPException(status_code=404,detail="Public continuity status is disabled.")
    return PublicEnvelope(data=continuity.public_status(db,request.app.state.settings,environment),meta={"api_version":"v1","request_id":request.state.request_id})
