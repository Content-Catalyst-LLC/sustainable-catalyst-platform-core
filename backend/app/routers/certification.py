from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..migrations import migration_status
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import certification
from ..models import RecoveryReadinessCheckpoint
router=APIRouter(prefix="/v1/certification", tags=["Production Certification, Migration Assurance & Recovery"])
public_router=APIRouter(prefix="/api/v1/certification", tags=["Unified Public API — Certification Readiness"])

def rowdict(row):
    return {"id":row.id,"release":row.release,"state":row.state,"migration_head":row.migration_head,"pending_migrations":row.pending_migrations_json,"checks":row.checks_json,"blockers":row.blockers_json,"gateway":row.gateway_json,"recovery":row.recovery_json,"certification_hash":row.certification_hash,"created_at":row.created_at,"completed_at":row.completed_at}

@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,db:Session=Depends(get_session)):
    d=certification.readiness(db,request.app.state.settings); m=certification.migration_assurance(request.app.state.database); d.update({"release":request.app.state.settings.version,"migration_0020_applied":"0020" in m['applied'],"migration_assurance":m,"promotion_requires_transient_external_provider_health":False}); return d

@router.get('/migration-assurance',dependencies=[Depends(require_read)])
def migration_assurance(request:Request): return certification.migration_assurance(request.app.state.database)

@router.post('/runs',dependencies=[Depends(require_write)])
async def run(request:Request,db:Session=Depends(get_session)):
    gateway=await request.app.state.gateway_runtime.health_snapshot(); row,detail=certification.run_certification(db,request.app.state.database,request.app.state.settings,gateway); return {"run":jsonable_encoder(rowdict(row)),"detail":jsonable_encoder(detail)}

@router.get('/runs',dependencies=[Depends(require_write)])
def runs(limit:int=Query(100,ge=1,le=1000),db:Session=Depends(get_session)): return {"items":jsonable_encoder([rowdict(x) for x in certification.list_runs(db,limit)])}

@router.post('/recovery/checkpoints',dependencies=[Depends(require_write)])
def checkpoint(request:Request,db:Session=Depends(get_session)):
    try:
        row=certification.create_recovery_checkpoint(db,request.app.state.database,request.app.state.settings); return jsonable_encoder({"id":row.id,"release":row.release,"schema_head":row.schema_head,"checkpoint_hash":row.checkpoint_hash,"recovery_contract":row.recovery_contract_json,"created_at":row.created_at,"expires_at":row.expires_at})
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))

@router.get('/recovery/checkpoints',dependencies=[Depends(require_write)])
def checkpoints(limit:int=Query(100,ge=1,le=1000),db:Session=Depends(get_session)): return {"items":jsonable_encoder([{"id":x.id,"release":x.release,"schema_head":x.schema_head,"checkpoint_hash":x.checkpoint_hash,"created_at":x.created_at,"expires_at":x.expires_at} for x in certification.list_checkpoints(db,limit)])}

@router.post('/recovery/checkpoints/{checkpoint_id}/verify',dependencies=[Depends(require_write)])
def verify(checkpoint_id:str,db:Session=Depends(get_session)):
    row=db.get(RecoveryReadinessCheckpoint,checkpoint_id)
    if not row: raise HTTPException(status_code=404,detail='Recovery checkpoint not found.')
    return certification.verify_recovery_checkpoint(row)

@public_router.get('/readiness')
def public_ready(request:Request,db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    d=certification.readiness(db,request.app.state.settings); m=certification.migration_assurance(request.app.state.database)
    safe={"enabled":d['enabled'],"release":request.app.state.settings.version,"schema_head":m['schema_head'],"expected_head":m['expected_head'],"zero_pending_migrations":m['zero_pending'],"recovery_checkpoint_enabled":d['recovery_checkpoint_enabled'],"database_backup_embedded":False,"external_provider_health_release_blocking":False,"certification_records_publicly_exposed":False}
    return PublicEnvelope(data=safe,meta={"api_version":"v1","request_id":request.state.request_id})
