from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..dependencies import get_session
from ..models import InvestigationWorkspace
from ..services import investigation_workspace as svc
router=APIRouter(prefix="/api/v1/investigation-workspace", tags=["Unified Investigation Workspace"])
class InvestigationIn(BaseModel): title:str=Field(min_length=1,max_length=300); description:str|None=None; domain:str|None=None
class ObjectIn(BaseModel): object_type:str; label:str; external_id:str|None=None; payload:dict={}; provenance:dict={}
class RelationIn(BaseModel): source_object_id:str; target_object_id:str; relation_type:str; confidence:int|None=Field(default=None,ge=0,le=100); rationale:str|None=None; payload:dict={}
class ViewIn(BaseModel): name:str; view_type:str; specification:dict={}
class HandoffIn(BaseModel): target_product:str
@router.get("/capabilities")
def capabilities(): return {"version":"3.20.0","capability":"Unified Investigation Workspace","objects":["investigation","evidence/reference object","explicit relation","analytical view","immutable snapshot","cross-product handoff"],"engines":["evidence","forensics","visual reasoning","predictive intelligence","reproducibility"]}
@router.post("/investigations")
def create(body:InvestigationIn,db:Session=Depends(get_session)):
    x=svc.create_investigation(db,body.title,body.description,body.domain); return {"id":x.id,"title":x.title,"status":x.status}
@router.get("/investigations")
def list_all(db:Session=Depends(get_session)):
    return [{"id":x.id,"title":x.title,"status":x.status,"domain":x.domain} for x in db.query(InvestigationWorkspace).order_by(InvestigationWorkspace.created_at.desc()).limit(250).all()]
@router.get("/investigations/{investigation_id}")
def get_one(investigation_id:str,db:Session=Depends(get_session)):
    m=svc.manifest(db,investigation_id)
    if m is None: raise HTTPException(404,"investigation not found")
    return m
@router.post("/investigations/{investigation_id}/objects")
def add_object(investigation_id:str,body:ObjectIn,db:Session=Depends(get_session)):
    if svc.manifest(db,investigation_id) is None: raise HTTPException(404,"investigation not found")
    x=svc.add_object(db,investigation_id,body.object_type,body.label,body.external_id,body.payload,body.provenance); return {"id":x.id}
@router.post("/investigations/{investigation_id}/relations")
def add_relation(investigation_id:str,body:RelationIn,db:Session=Depends(get_session)):
    x=svc.add_relation(db,investigation_id,body.source_object_id,body.target_object_id,body.relation_type,body.confidence,body.rationale,body.payload); return {"id":x.id}
@router.post("/investigations/{investigation_id}/views")
def add_view(investigation_id:str,body:ViewIn,db:Session=Depends(get_session)):
    x=svc.add_view(db,investigation_id,body.name,body.view_type,body.specification); return {"id":x.id}
@router.get("/investigations/{investigation_id}/map")
def map_view(investigation_id:str,db:Session=Depends(get_session)):
    m=svc.manifest(db,investigation_id)
    if m is None: raise HTTPException(404,"investigation not found")
    return {"investigation":m["investigation"],"nodes":m["objects"],"edges":m["relations"],"views":m["views"]}
@router.get("/investigations/{investigation_id}/diagnostics")
def diag(investigation_id:str,db:Session=Depends(get_session)):
    d=svc.diagnostics(db,investigation_id)
    if d is None: raise HTTPException(404,"investigation not found")
    return d
@router.post("/investigations/{investigation_id}/snapshots")
def snapshot(investigation_id:str,db:Session=Depends(get_session)):
    if svc.manifest(db,investigation_id) is None: raise HTTPException(404,"investigation not found")
    x=svc.create_snapshot(db,investigation_id); return {"id":x.id,"sha256":x.manifest_sha256}
@router.post("/investigations/{investigation_id}/handoffs")
def handoff(investigation_id:str,body:HandoffIn,db:Session=Depends(get_session)):
    if svc.manifest(db,investigation_id) is None: raise HTTPException(404,"investigation not found")
    x,b=svc.create_handoff(db,investigation_id,body.target_product); return {"id":x.id,"bundle":b}
