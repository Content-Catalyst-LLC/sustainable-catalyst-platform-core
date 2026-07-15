from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter,Depends,Query,Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from ..dependencies import get_session,require_read
from ..public_api_auth import PublicApiContext,require_public_scope
from ..schemas import EconomicDataRecordRead,EconomicDataStats,PublicEnvelope
from ..services.economic_data import ECONOMIC_RECORD_TYPES,get_record_or_404,list_records,provenance,stats
router=APIRouter(prefix="/v1/economics",tags=["Economics and Official Statistics Connector Pack"])
public_router=APIRouter(prefix="/api/v1/economics",tags=["Unified Public API — Economics"])
def envelope(request:Request,data,*,meta=None):
    payload={"api_version":"v1","request_id":request.state.request_id,"documentation":"/docs#tag/Unified-Public-API-Economics"}
    if meta: payload.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data),meta=payload)
@router.get('/records',response_model=dict,dependencies=[Depends(require_read)])
def records(record_type:str|None=None,subject:str|None=None,source_id:str|None=None,connector_id:str|None=None,indicator_code:str|None=None,dataset_id:str|None=None,geography_code:str|None=None,frequency:str|None=None,query:str|None=None,start:datetime|None=None,end:datetime|None=None,limit:int=Query(default=100,ge=1,le=1000),offset:int=Query(default=0,ge=0),db:Session=Depends(get_session)):
    rows,total=list_records(db,record_type=record_type,subject=subject,source_id=source_id,connector_id=connector_id,indicator_code=indicator_code,dataset_id=dataset_id,geography_code=geography_code,frequency=frequency,query=query,start=start,end=end,limit=limit,offset=offset)
    return {"items":[EconomicDataRecordRead.model_validate(row).model_dump(mode='json',by_alias=True) for row in rows],"total":total,"limit":limit,"offset":offset}
@router.get('/records/{record_id}',response_model=EconomicDataRecordRead,dependencies=[Depends(require_read)])
def record(record_id:str,db:Session=Depends(get_session)): return get_record_or_404(db,record_id)
@router.get('/provenance/{record_id}',response_model=dict,dependencies=[Depends(require_read)])
def record_provenance(record_id:str,db:Session=Depends(get_session)): return jsonable_encoder(provenance(db,get_record_or_404(db,record_id)))
@router.get('/record-types',response_model=dict,dependencies=[Depends(require_read)])
def record_types(): return ECONOMIC_RECORD_TYPES
@router.get('/stats',response_model=EconomicDataStats,dependencies=[Depends(require_read)])
def record_stats(db:Session=Depends(get_session)): return stats(db)
@public_router.get('/records',response_model=PublicEnvelope)
def public_records(request:Request,record_type:str|None=None,subject:str|None=None,source_id:str|None=None,connector_id:str|None=None,indicator_code:str|None=None,dataset_id:str|None=None,geography_code:str|None=None,frequency:str|None=None,query:str|None=None,start:datetime|None=None,end:datetime|None=None,limit:int=Query(default=100,ge=1),offset:int=Query(default=0,ge=0),context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    limit=min(limit,context.plan.max_page_size,request.app.state.settings.page_size_max)
    rows,total=list_records(db,record_type=record_type,subject=subject,source_id=source_id,connector_id=connector_id,indicator_code=indicator_code,dataset_id=dataset_id,geography_code=geography_code,frequency=frequency,query=query,start=start,end=end,public_only=True,limit=limit,offset=offset)
    return envelope(request,[EconomicDataRecordRead.model_validate(row) for row in rows],meta={"pagination":{"total":total,"limit":limit,"offset":offset}})
@public_router.get('/records/{record_id}',response_model=PublicEnvelope)
def public_record(request:Request,record_id:str,_context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)): return envelope(request,EconomicDataRecordRead.model_validate(get_record_or_404(db,record_id,public_only=True)))
@public_router.get('/record-types',response_model=PublicEnvelope)
def public_types(request:Request,_context:PublicApiContext=Depends(require_public_scope('data:read'))): return envelope(request,ECONOMIC_RECORD_TYPES)
