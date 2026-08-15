from __future__ import annotations
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..models import FacilityObservation, FacilitySourceIdentifier, OperationalFacility
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services.facilities import FACILITY_TYPES, OBSERVATION_KINDS, create_facility, create_observation, current_observations, query_facilities

router=APIRouter(prefix="/v1/facilities", tags=["Operational Evidence & Facility Registry"])
public_router=APIRouter(prefix="/api/v1/facilities", tags=["Unified Public API — Facilities"])

class SourceIdentifierIn(BaseModel):
    namespace: str = Field(min_length=1,max_length=160); value: str = Field(min_length=1,max_length=700); source_id: str|None=None
class FacilityCreate(BaseModel):
    name: str=Field(min_length=1,max_length=500); facility_type: str; country_code: str=Field(min_length=3,max_length=3); admin_area: str|None=None; locality: str|None=None; latitude: float|None=None; longitude: float|None=None; geometry: dict[str,Any]|None=None; canonical_entity_id: str|None=None; source_identifiers: list[SourceIdentifierIn]=Field(default_factory=list); public: bool=True; metadata: dict[str,Any]=Field(default_factory=dict)
class ObservationCreate(BaseModel):
    observation_kind: str; status_value: str=Field(min_length=1,max_length=120); observed_at: datetime; publisher: str=Field(min_length=1,max_length=400); source_id: str|None=None; connector_id: str|None=None; source_record_id: str|None=None; source_url: str|None=None; evidence_class: str="published-evidence"; geographic_scope: str|None=None; methodology: str|None=None; confidence: float|None=Field(default=None,ge=0,le=1); services: list[Any]=Field(default_factory=list); constraints: list[Any]=Field(default_factory=list); details: dict[str,Any]=Field(default_factory=dict); provenance: dict[str,Any]=Field(default_factory=dict); public: bool=True

def _facility(row, identifiers=None):
    return {"id":row.id,"canonical_entity_id":row.canonical_entity_id,"name":row.name,"facility_type":row.facility_type,"country_code":row.country_code,"admin_area":row.admin_area,"locality":row.locality,"latitude":row.latitude,"longitude":row.longitude,"geometry":row.geometry_json,"registry_status":row.registry_status,"public":row.public,"metadata":row.metadata_json,"source_identifiers":identifiers or [],"created_at":row.created_at,"updated_at":row.updated_at}
def _observation(row):
    return {"id":row.id,"facility_id":row.facility_id,"observation_kind":row.observation_kind,"status_value":row.status_value,"observed_at":row.observed_at,"publisher":row.publisher,"source_id":row.source_id,"connector_id":row.connector_id,"source_record_id":row.source_record_id,"source_url":row.source_url,"evidence_class":row.evidence_class,"geographic_scope":row.geographic_scope,"methodology":row.methodology,"confidence":row.confidence,"services":row.services_json,"constraints":row.constraints_json,"details":row.details_json,"provenance":row.provenance_json,"public":row.public,"created_at":row.created_at}
def _bbox(raw):
    if not raw:return None
    try: vals=tuple(float(x.strip()) for x in raw.split(','))
    except Exception: raise HTTPException(status_code=422, detail="bbox must contain four comma-separated numbers")
    if len(vals)!=4: raise HTTPException(status_code=422, detail="bbox must contain four comma-separated numbers")
    return vals

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request:Request, db:Session=Depends(get_session)):
    return {"release":request.app.state.settings.version,"migration_0013_applied":True,"facility_types":sorted(FACILITY_TYPES),"observation_kinds":sorted(OBSERVATION_KINDS),"facilities":len(db.scalars(select(OperationalFacility.id)).all()),"observations":len(db.scalars(select(FacilityObservation.id)).all()),"history_preserving":True,"automatic_conflict_flattening":False,"status":"ready"}
@router.post("", dependencies=[Depends(require_write)])
def create(payload:FacilityCreate, db:Session=Depends(get_session)):
    try: row=create_facility(db, **payload.model_dump(exclude={"source_identifiers"}), source_identifiers=[x.model_dump() for x in payload.source_identifiers])
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))
    ids=db.scalars(select(FacilitySourceIdentifier).where(FacilitySourceIdentifier.facility_id==row.id)).all(); return _facility(row,[{"namespace":x.namespace,"value":x.value,"source_id":x.source_id} for x in ids])
@router.get("", dependencies=[Depends(require_read)])
def list_internal(country_code:str|None=None, facility_type:str|None=None, admin_area:str|None=None, bbox:str|None=None, limit:int=Query(200,ge=1,le=1000), db:Session=Depends(get_session)):
    try: rows=query_facilities(db,country_code=country_code,facility_type=facility_type,admin_area=admin_area,bbox=_bbox(bbox),limit=limit)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
    return {"items":[_facility(x) for x in rows],"total":len(rows)}
@public_router.get("")
def list_public(country_code:str|None=None, facility_type:str|None=None, admin_area:str|None=None, bbox:str|None=None, limit:int=Query(200,ge=1,le=1000), _context:PublicApiContext=Depends(require_public_scope("data:read")), db:Session=Depends(get_session)):
    try: rows=query_facilities(db,country_code=country_code,facility_type=facility_type,admin_area=admin_area,bbox=_bbox(bbox),public_only=True,limit=limit)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
    return {"items":[_facility(x) for x in rows],"total":len(rows)}
@router.get("/{facility_id}", dependencies=[Depends(require_read)])
def get_one(facility_id:str,db:Session=Depends(get_session)):
    row=db.get(OperationalFacility,facility_id)
    if not row: raise HTTPException(404,"facility not found")
    ids=db.scalars(select(FacilitySourceIdentifier).where(FacilitySourceIdentifier.facility_id==row.id)).all(); data=_facility(row,[{"namespace":x.namespace,"value":x.value,"source_id":x.source_id} for x in ids]); data["current_observations"]=[_observation(x) for x in current_observations(db,row.id)]; return data
@public_router.get("/{facility_id}")
def public_get_one(facility_id:str,_context:PublicApiContext=Depends(require_public_scope("data:read")),db:Session=Depends(get_session)):
    row=db.get(OperationalFacility,facility_id)
    if not row or not row.public: raise HTTPException(404,"facility not found")
    ids=db.scalars(select(FacilitySourceIdentifier).where(FacilitySourceIdentifier.facility_id==row.id)).all()
    data=_facility(row,[{"namespace":x.namespace,"value":x.value,"source_id":x.source_id} for x in ids])
    data["current_observations"]=[_observation(x) for x in current_observations(db,row.id,public_only=True)]
    return data

@router.post("/{facility_id}/observations", dependencies=[Depends(require_write)])
def add_observation(facility_id:str,payload:ObservationCreate,db:Session=Depends(get_session)):
    try: row=create_observation(db,facility_id,**payload.model_dump())
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
    return _observation(row)
@router.get("/{facility_id}/observations", dependencies=[Depends(require_read)])
def history(facility_id:str,kind:str|None=None,limit:int=Query(200,ge=1,le=1000),db:Session=Depends(get_session)):
    q=select(FacilityObservation).where(FacilityObservation.facility_id==facility_id)
    if kind:q=q.where(FacilityObservation.observation_kind==kind)
    rows=db.scalars(q.order_by(desc(FacilityObservation.observed_at)).limit(limit)).all(); return {"items":[_observation(x) for x in rows],"total":len(rows)}
@public_router.get("/{facility_id}/observations")
def public_history(facility_id:str,kind:str|None=None,limit:int=Query(200,ge=1,le=1000),_context:PublicApiContext=Depends(require_public_scope("data:read")),db:Session=Depends(get_session)):
    facility=db.get(OperationalFacility,facility_id)
    if not facility or not facility.public: raise HTTPException(404,"facility not found")
    q=select(FacilityObservation).where(FacilityObservation.facility_id==facility_id,FacilityObservation.public.is_(True))
    if kind:q=q.where(FacilityObservation.observation_kind==kind)
    rows=db.scalars(q.order_by(desc(FacilityObservation.observed_at)).limit(limit)).all(); return {"items":[_observation(x) for x in rows],"total":len(rows)}
