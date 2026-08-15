from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import scale

router=APIRouter(prefix="/v1/scale", tags=["Distributed Processing, Storage & Scale"])
public_router=APIRouter(prefix="/api/v1/scale", tags=["Unified Public API — Scale Readiness"])
class PartitionCreate(BaseModel): key:str|None=None; payload:dict=Field(default_factory=dict); max_attempts:int=3
class JobCreate(BaseModel):
    job_type:str; origin_product:str="platform-core"; idempotency_key:str=Field(min_length=1,max_length=128); priority:int=100; parameters:dict=Field(default_factory=dict); metadata:dict=Field(default_factory=dict); partitions:list[PartitionCreate]=Field(min_length=1,max_length=10000)
class CompleteCreate(BaseModel): result:dict=Field(default_factory=dict); external_uri:str|None=None; provenance:dict=Field(default_factory=dict)
class FailCreate(BaseModel): error:str

def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    d=scale.readiness(db,request.app.state.settings); m=migration_status(request.app.state.database); d.update({"release":request.app.state.settings.version,"migration_0018_applied":"0018" in m["applied"],"partition_leases":True,"retention_compaction":True,"evidence_semantics_unchanged":True}); return d
@router.post('/jobs',dependencies=[Depends(require_write)])
def create(payload:JobCreate,request:Request,db:Session=Depends(get_session)):
    try:
        row=scale.create_job(db,request.app.state.settings,**payload.model_dump(exclude={'partitions'}),partitions=[p.model_dump() for p in payload.partitions]); return scale.job_detail(db,row.id)
    except ValueError as e: raise bad(e)
@router.get('/jobs/{job_id}',dependencies=[Depends(require_read)])
def detail(job_id:str,db:Session=Depends(get_session)):
    try:return scale.job_detail(db,job_id)
    except ValueError as e: raise HTTPException(status_code=404,detail=str(e))
@router.post('/partitions/claim',dependencies=[Depends(require_write)])
def claim(request:Request,worker_id:str='core-worker',db:Session=Depends(get_session)):
    row=scale.claim_partition(db,request.app.state.settings,worker_id); return {"item":None} if not row else {"item":{"id":row.id,"job_id":row.job_id,"partition_key":row.partition_key,"payload":row.payload_json,"attempt_count":row.attempt_count,"lease_expires_at":row.lease_expires_at}}
@router.post('/partitions/{partition_id}/complete',dependencies=[Depends(require_write)])
def complete(partition_id:str,payload:CompleteCreate,request:Request,db:Session=Depends(get_session)):
    try:
        row,obj=scale.complete_partition(db,request.app.state.settings,partition_id,**payload.model_dump()); return {"partition_id":row.id,"state":row.state,"storage_object":{"id":obj.id,"storage_class":obj.storage_class,"byte_size":obj.byte_size,"content_hash":obj.content_hash}}
    except ValueError as e: raise bad(e)
@router.post('/partitions/{partition_id}/fail',dependencies=[Depends(require_write)])
def fail(partition_id:str,payload:FailCreate,db:Session=Depends(get_session)):
    try:r=scale.fail_partition(db,partition_id,payload.error); return {"partition_id":r.id,"state":r.state,"attempt_count":r.attempt_count}
    except ValueError as e: raise bad(e)
@router.post('/storage/compact',dependencies=[Depends(require_write)])
def compact(db:Session=Depends(get_session)): return {"compacted":scale.compact_expired_storage(db)}
@public_router.get('/readiness')
def public_ready(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    d=scale.readiness(db,request.app.state.settings); safe={k:d[k] for k in ('enabled','active_jobs','queued_partitions','claimed_partitions','backpressure','max_active_jobs','max_partitions_per_job','storage_classes','external_blob_provider_required')}; safe.update({"release":request.app.state.settings.version,"job_payloads_publicly_exposed":False}); return PublicEnvelope(data=safe,meta={"api_version":"v1","request_id":request.state.request_id})
