from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import MapLayerRead, PublicEnvelope, ScientificDataAssetRead, ScientificDataRecordRead, TimeSeriesDefinitionRead
from ..migrations import migration_status
from ..services.scientific_service_fabric import DOMAINS, domain_summary, list_domain_assets, list_domain_layers, list_domain_records, list_domain_series, materialize

router=APIRouter(prefix="/v1/scientific-fabric",tags=["Earth, Ocean, Space & Scientific Service Fabric"])
public_router=APIRouter(prefix="/api/v1/scientific-fabric",tags=["Unified Public API — Scientific Service Fabric"])

def envelope(request:Request,data,*,meta:dict|None=None)->PublicEnvelope:
    payload={"api_version":"v1","request_id":request.state.request_id,"documentation":"/docs#tag/Unified-Public-API-Scientific-Service-Fabric"}
    if meta:payload.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data),meta=payload)

@router.get('/readiness',dependencies=[Depends(require_read)])
def readiness(request:Request,db:Session=Depends(get_session)):
    summaries={domain:domain_summary(db,domain) for domain in DOMAINS}
    status=migration_status(request.app.state.database)
    return {"status":"ready" if request.app.state.settings.scientific_service_fabric_enabled else "disabled","release":request.app.state.settings.version,"migration_0016_applied":"0016" in status["applied"],"domains":list(DOMAINS),"domain_summaries":summaries,"routing_only":True,"truth_precedence":"none","automatic_cross_domain_blending":False,"zero_records_implication":"no-routed-records-not-no-science"}

@router.post('/materialize',dependencies=[Depends(require_write)])
def materialize_route(db:Session=Depends(get_session)):return materialize(db)

@router.get('/domains',dependencies=[Depends(require_read)])
def domains(db:Session=Depends(get_session)):return {"items":[domain_summary(db,d) for d in DOMAINS]}

@router.get('/domains/{domain}',dependencies=[Depends(require_read)])
def domain(domain:str,db:Session=Depends(get_session)):return domain_summary(db,domain)

@router.get('/domains/{domain}/records',dependencies=[Depends(require_read)])
def records(domain:str,mission:str|None=None,subdomain:str|None=None,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    rows,total=list_domain_records(db,domain,mission=mission,subdomain=subdomain,limit=limit,offset=offset);return {"items":[ScientificDataRecordRead.model_validate(x) for x in rows],"total":total,"limit":limit,"offset":offset}

@router.get('/domains/{domain}/assets',dependencies=[Depends(require_read)])
def assets(domain:str,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    rows,total=list_domain_assets(db,domain,limit=limit,offset=offset);return {"items":[ScientificDataAssetRead.model_validate(x) for x in rows],"total":total,"limit":limit,"offset":offset}

@router.get('/domains/{domain}/timeseries',dependencies=[Depends(require_read)])
def series(domain:str,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    rows,total=list_domain_series(db,domain,limit=limit,offset=offset);return {"items":[TimeSeriesDefinitionRead.model_validate(x) for x in rows],"total":total,"limit":limit,"offset":offset}

@router.get('/domains/{domain}/map-layers',dependencies=[Depends(require_read)])
def layers(domain:str,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_session)):
    rows,total=list_domain_layers(db,domain,limit=limit,offset=offset);return {"items":[MapLayerRead.model_validate(x) for x in rows],"total":total,"limit":limit,"offset":offset}

@public_router.get('/domains')
def public_domains(request:Request,_context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):return envelope(request,[domain_summary(db,d,public_only=True) for d in DOMAINS])

@public_router.get('/domains/{domain}')
def public_domain(request:Request,domain:str,_context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):return envelope(request,domain_summary(db,domain,public_only=True))

@public_router.get('/domains/{domain}/records')
def public_records(request:Request,domain:str,mission:str|None=None,subdomain:str|None=None,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    limit=min(limit,context.plan.max_page_size,request.app.state.settings.page_size_max);rows,total=list_domain_records(db,domain,public_only=True,mission=mission,subdomain=subdomain,limit=limit,offset=offset);return envelope(request,[ScientificDataRecordRead.model_validate(x) for x in rows],meta={"pagination":{"total":total,"limit":limit,"offset":offset}})

@public_router.get('/domains/{domain}/assets')
def public_assets(request:Request,domain:str,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    limit=min(limit,context.plan.max_page_size,request.app.state.settings.page_size_max);rows,total=list_domain_assets(db,domain,public_only=True,limit=limit,offset=offset);return envelope(request,[ScientificDataAssetRead.model_validate(x) for x in rows],meta={"pagination":{"total":total,"limit":limit,"offset":offset}})

@public_router.get('/domains/{domain}/timeseries')
def public_series(request:Request,domain:str,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    limit=min(limit,context.plan.max_page_size,request.app.state.settings.page_size_max);rows,total=list_domain_series(db,domain,public_only=True,limit=limit,offset=offset);return envelope(request,[TimeSeriesDefinitionRead.model_validate(x) for x in rows],meta={"pagination":{"total":total,"limit":limit,"offset":offset}})

@public_router.get('/domains/{domain}/map-layers')
def public_layers(request:Request,domain:str,limit:int=Query(100,ge=1),offset:int=Query(0,ge=0),context:PublicApiContext=Depends(require_public_scope('data:read')),db:Session=Depends(get_session)):
    limit=min(limit,context.plan.max_page_size,request.app.state.settings.page_size_max);rows,total=list_domain_layers(db,domain,public_only=True,limit=limit,offset=offset);return envelope(request,[MapLayerRead.model_validate(x) for x in rows],meta={"pagination":{"total":total,"limit":limit,"offset":offset}})
