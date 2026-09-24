from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import InvestigationWorkspace, InvestigationWorkspaceObject, InvestigationWorkspaceRelation, InvestigationWorkspaceView, InvestigationWorkspaceSnapshot, InvestigationWorkspaceHandoff

def _id(prefix:str)->str: return f"{prefix}_{uuid.uuid4().hex}"
def _j(v)->str: return json.dumps(v or {}, sort_keys=True, separators=(",",":"), default=str)
def _loads(v):
    try: return json.loads(v or "{}")
    except Exception: return {}

def create_investigation(db:Session, title:str, description=None, domain=None):
    row=InvestigationWorkspace(id=_id("inv"), title=title, description=description, domain=domain, status="active")
    db.add(row); db.commit(); db.refresh(row); return row

def add_object(db:Session, investigation_id:str, object_type:str, label:str, external_id=None, payload=None, provenance=None):
    row=InvestigationWorkspaceObject(id=_id("obj"), investigation_id=investigation_id, object_type=object_type, external_id=external_id, label=label, payload_json=_j(payload), provenance_json=_j(provenance))
    db.add(row); db.commit(); db.refresh(row); return row

def add_relation(db:Session, investigation_id:str, source_object_id:str, target_object_id:str, relation_type:str, confidence=None, rationale=None, payload=None):
    row=InvestigationWorkspaceRelation(id=_id("rel"), investigation_id=investigation_id, source_object_id=source_object_id, target_object_id=target_object_id, relation_type=relation_type, confidence=confidence, rationale=rationale, payload_json=_j(payload))
    db.add(row); db.commit(); db.refresh(row); return row

def add_view(db:Session, investigation_id:str, name:str, view_type:str, specification=None):
    row=InvestigationWorkspaceView(id=_id("view"), investigation_id=investigation_id, name=name, view_type=view_type, specification_json=_j(specification))
    db.add(row); db.commit(); db.refresh(row); return row

def manifest(db:Session, investigation_id:str):
    inv=db.get(InvestigationWorkspace, investigation_id)
    if not inv: return None
    objects=db.query(InvestigationWorkspaceObject).filter_by(investigation_id=investigation_id).all()
    relations=db.query(InvestigationWorkspaceRelation).filter_by(investigation_id=investigation_id).all()
    views=db.query(InvestigationWorkspaceView).filter_by(investigation_id=investigation_id).all()
    return {"version":"3.20.0","investigation":{"id":inv.id,"title":inv.title,"description":inv.description,"status":inv.status,"domain":inv.domain},"objects":[{"id":x.id,"type":x.object_type,"external_id":x.external_id,"label":x.label,"payload":_loads(x.payload_json),"provenance":_loads(x.provenance_json)} for x in objects],"relations":[{"id":x.id,"source":x.source_object_id,"target":x.target_object_id,"type":x.relation_type,"confidence":x.confidence,"rationale":x.rationale,"payload":_loads(x.payload_json)} for x in relations],"views":[{"id":x.id,"name":x.name,"type":x.view_type,"specification":_loads(x.specification_json)} for x in views]}

def diagnostics(db:Session, investigation_id:str):
    m=manifest(db, investigation_id)
    if m is None: return None
    ids={x["id"] for x in m["objects"]}; dangling=[r["id"] for r in m["relations"] if r["source"] not in ids or r["target"] not in ids]
    by_type={}
    for x in m["objects"]: by_type[x["type"]]=by_type.get(x["type"],0)+1
    return {"investigation_id":investigation_id,"object_count":len(m["objects"]),"relation_count":len(m["relations"]),"view_count":len(m["views"]),"objects_by_type":by_type,"dangling_relation_ids":dangling,"integrity":"ok" if not dangling else "warning"}

def create_snapshot(db:Session, investigation_id:str):
    m=manifest(db, investigation_id); canonical=_j(m); digest=hashlib.sha256(canonical.encode()).hexdigest()
    row=InvestigationWorkspaceSnapshot(id=_id("snap"), investigation_id=investigation_id, manifest_json=canonical, manifest_sha256=digest)
    db.add(row); db.commit(); db.refresh(row); return row

def create_handoff(db:Session, investigation_id:str, target_product:str):
    m=manifest(db, investigation_id); d=diagnostics(db, investigation_id); bundle={"schema":"sc.investigation-handoff/1","core_version":"3.20.0","target_product":target_product,"manifest":m,"diagnostics":d}
    row=InvestigationWorkspaceHandoff(id=_id("handoff"), investigation_id=investigation_id, target_product=target_product, bundle_json=_j(bundle))
    db.add(row); db.commit(); db.refresh(row); return row, bundle
