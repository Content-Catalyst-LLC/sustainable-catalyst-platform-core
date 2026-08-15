from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read,require_write
from ..migrations import migration_status
from ..models import FailoverGroupRecord,FailoverAssessmentRecord
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import PublicEnvelope
from ..services import resilience
router=APIRouter(prefix="/v1/resilience",tags=["Multi-Region Resilience & Failover Coordination"])
public_router=APIRouter(prefix="/api/v1/resilience",tags=["Unified Public API — Resilience Status"])
class RegionUpsert(BaseModel):
    region_key:str=Field(min_length=1,max_length=100); service:str="platform-core"; environment:str="production"; role:str="standby"; health_state:str="unknown"; readiness_state:str="unknown"; replication_state:str="unknown"; replication_lag_seconds:int|None=None; read_eligible:bool=False; write_eligible:bool=False; recovery_priority:int=100; endpoint_ref:str|None=None; metadata:dict=Field(default_factory=dict)
class GroupCreate(BaseModel):
    group_key:str=Field(min_length=1,max_length=255); active_region:str; candidate_regions:list[str]; service:str="platform-core"; environment:str="production"; strategy:str="operator-coordinated"; degraded_read_only_allowed:bool|None=None; max_replication_lag_seconds:int|None=None; metadata:dict=Field(default_factory=dict)
class Assess(BaseModel): reason:str="operator-request"
class Decision(BaseModel): state:str; actor:str="operator"
def rowdict(row): return {c.key:getattr(row,c.key) for c in row.__table__.columns}
def bad(e): return HTTPException(status_code=422,detail=str(e))
@router.get('/readiness',dependencies=[Depends(require_read)])
def ready(request:Request,environment:str='production',db:Session=Depends(get_session)):
    s=resilience.readiness(db,request.app.state.settings,environment); m=migration_status(request.app.state.database); s.update({"release":request.app.state.settings.version,"migration_0024_applied":"0024" in m["applied"],"pending_migrations":m["pending"]}); return s
@router.post('/regions',dependencies=[Depends(require_write)])
def region(payload:RegionUpsert,db:Session=Depends(get_session)):
    try:return rowdict(resilience.upsert_region_status(db,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/regions',dependencies=[Depends(require_read)])
def regions(service:str|None=None,environment:str|None=None,db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in resilience.list_regions(db,service,environment)]}
@router.post('/failover-groups',dependencies=[Depends(require_write)])
def group(request:Request,payload:GroupCreate,db:Session=Depends(get_session)):
    try:return rowdict(resilience.create_group(db,request.app.state.settings,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@router.get('/failover-groups',dependencies=[Depends(require_read)])
def groups(environment:str|None=None,db:Session=Depends(get_session)): return {"items":[rowdict(x) for x in resilience.list_groups(db,environment)]}
@router.post('/failover-groups/{group_id}/assess',dependencies=[Depends(require_write)])
def assess(group_id:str,payload:Assess,db:Session=Depends(get_session)):
    g=db.get(FailoverGroupRecord,group_id)
    if not g: raise HTTPException(status_code=404,detail="Failover group not found.")
    return rowdict(resilience.assess_failover(db,g,reason=payload.reason))
@router.post('/failovers/{assessment_id}/decision',dependencies=[Depends(require_write)])
def decide(assessment_id:str,payload:Decision,db:Session=Depends(get_session)):
    row=db.get(FailoverAssessmentRecord,assessment_id)
    if not row: raise HTTPException(status_code=404,detail="Failover assessment not found.")
    try:return rowdict(resilience.decide_failover(db,row,**payload.model_dump()))
    except ValueError as e: raise bad(e)
@public_router.get('/status')
def public_status(request:Request,environment:str='production',db:Session=Depends(get_session),_context:PublicApiContext=Depends(require_public_scope('data:read'))):
    if not request.app.state.settings.multi_region_public_status_enabled: raise HTTPException(status_code=404,detail="Public resilience status is disabled.")
    return PublicEnvelope(data=resilience.public_status(db,request.app.state.settings,environment),meta={"api_version":"v1","request_id":request.state.request_id})
