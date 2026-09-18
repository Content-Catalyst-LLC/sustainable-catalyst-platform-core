from __future__ import annotations
import hashlib, json, re
from datetime import datetime
from sqlalchemy import func, select, inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    Entity, ResearchProjectRecord,
    UnifiedResearchProjectProfileRecord, UnifiedResearchQuestionRecord,
    UnifiedResearchObjectiveRecord, UnifiedResearchComponentRecord,
    UnifiedResearchRelationshipRecord, UnifiedResearchProvenanceRecord,
    UnifiedResearchRuntimeHandoffRecord, UnifiedResearchProjectSnapshotRecord,
)
from . import research_objects

CONTRACT = "sc.research.unified-project.v1"
COMPONENT_KINDS = {
    "literature", "source_collection", "dataset", "evidence", "methodology",
    "model", "analysis_run", "finding", "visualization", "investigation",
    "conclusion", "limitation", "unresolved_question",
}
PRODUCTS = {"library", "lab", "workbench", "decision-studio", "site-intelligence", "workspace", "research-librarian", "platform-core", "external"}
FORBIDDEN = {
    "execute_analysis_by_core", "generate_findings_by_core", "promote_conclusion_by_core",
    "infer_originality_by_core", "automatic_truth_promotion", "execute_handoff_by_core",
}

def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key); out[a.key]=v.isoformat() if isinstance(v,datetime) else v
    for k in list(out):
        if k.endswith("_json"): out[k[:-5]]=out.pop(k)
    return out

def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _slug(v): return re.sub(r"[^a-z0-9]+","-",v.lower()).strip("-")[:180] or "research-project"
def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad: raise ValueError("Unified Research Project is declarative; Core does not execute: "+", ".join(bad))

def boundaries():
    return {
        "research_project_registry_by_core": True, "question_registry_by_core": True,
        "objective_registry_by_core": True, "typed_component_registry_by_core": True,
        "research_relationship_registry_by_core": True, "research_provenance_registry_by_core": True,
        "runtime_handoff_registry_by_core": True, "immutable_project_snapshots_by_core": True,
        "execute_analysis_by_core": False, "generate_findings_by_core": False,
        "promote_conclusion_by_core": False, "infer_originality_by_core": False,
        "automatic_truth_promotion": False, "execute_handoff_by_core": False,
    }

CLASSES=[UnifiedResearchProjectProfileRecord,UnifiedResearchQuestionRecord,UnifiedResearchObjectiveRecord,UnifiedResearchComponentRecord,UnifiedResearchRelationshipRecord,UnifiedResearchProvenanceRecord,UnifiedResearchRuntimeHandoffRecord,UnifiedResearchProjectSnapshotRecord]
NAMES=["profiles","questions","objectives","components","relationships","provenance_records","handoffs","snapshots"]

def readiness(db:Session):
    c=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {"release":"2.72.0","contract":CONTRACT,"component_kinds":sorted(COMPONENT_KINDS),"products":sorted(PRODUCTS),"counts":dict(zip(NAMES,[c(x) for x in CLASSES])),**boundaries()}

def _base(db:Session,project_id:str):
    ent=db.get(Entity,project_id); base=db.get(ResearchProjectRecord,project_id)
    if ent is None or ent.entity_type!="research-project" or base is None: raise ValueError("project_entity_id must reference an existing research-project.")
    return ent,base

def _profile(db:Session,project_id:str):
    row=db.get(UnifiedResearchProjectProfileRecord,project_id)
    if row is None: raise ValueError("unified research project profile not found.")
    return row

def adopt_project(db:Session,project_id:str,p:dict):
    _reject(p); ent,base=_base(db,project_id)
    if db.get(UnifiedResearchProjectProfileRecord,project_id): raise ValueError("unified research project profile already exists.")
    row=UnifiedResearchProjectProfileRecord(project_entity_id=project_id,project_key=p.get("project_key") or ent.slug,title=p.get("title") or ent.name,abstract=p.get("abstract") or ent.description,research_type=p.get("research_type","general"),lifecycle_state=p.get("lifecycle_state") or base.lifecycle_state,visibility=p.get("visibility") or ent.visibility,owner_product=p.get("owner_product") or base.owner_product,reproducibility_target=p.get("reproducibility_target") or base.reproducibility_target,scope_json=p.get("scope",{}),ethics_json=p.get("ethics",{}),governance_json=p.get("governance",{}),metadata_json=p.get("metadata",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def create_project(db:Session,p:dict):
    _reject(p)
    name=str(p.get("title") or "").strip()
    if not name: raise ValueError("title is required.")
    project_id=p.get("project_entity_id")
    created=research_objects.create_object(db,object_type="research-project",name=name,slug=p.get("project_key") or _slug(name),description=p.get("abstract"),entity_id=project_id,visibility=p.get("visibility","private"),entity_status=p.get("status","active"),attributes={"research_question":p.get("research_question"),"objective":p.get("objective"),"methodology":p.get("methodology"),"owner_product":p.get("owner_product","workspace"),"lifecycle_state":p.get("lifecycle_state","draft"),"reproducibility_target":p.get("reproducibility_target","reproducible"),"metadata":{"unified_research_project":"v2.72.0"}},metadata=p.get("metadata",{}),release="2.72.0")
    adopt=adopt_project(db,created["id"],p)
    return {"project":created,"unified_profile":adopt}

def question(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id)
    row=UnifiedResearchQuestionRecord(project_entity_id=project_id,question_key=p["question_key"],question_text=p["question_text"],question_type=p.get("question_type","primary"),status=p.get("status","open"),parent_question_id=p.get("parent_question_id"),rationale_json=p.get("rationale",{}),provenance_json=p.get("provenance",{})); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def objective(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id)
    row=UnifiedResearchObjectiveRecord(project_entity_id=project_id,objective_key=p["objective_key"],objective_text=p["objective_text"],objective_type=p.get("objective_type","research"),status=p.get("status","active"),success_criteria_json=p.get("success_criteria",[]),provenance_json=p.get("provenance",{})); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def component(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id); kind=p["component_kind"]
    if kind not in COMPONENT_KINDS: raise ValueError("unsupported research component kind: "+kind)
    product=p.get("product_key")
    if product and product not in PRODUCTS: raise ValueError("unsupported Catalyst product: "+product)
    row=UnifiedResearchComponentRecord(project_entity_id=project_id,component_key=p["component_key"],component_kind=kind,title=p["title"],status=p.get("status","declared"),canonical_ref=p.get("canonical_ref"),product_key=product,product_ref=p.get("product_ref"),content_json=p.get("content",{}),provenance_json=p.get("provenance",{}),metadata_json=p.get("metadata",{})); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def relationship(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id)
    row=UnifiedResearchRelationshipRecord(project_entity_id=project_id,subject_ref=p["subject_ref"],predicate=p["predicate"],object_ref=p["object_ref"],status=p.get("status","asserted"),evidence_refs_json=p.get("evidence_refs",[]),uncertainty_json=p.get("uncertainty",{}),provenance_json=p.get("provenance",{})); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def provenance(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id)
    row=UnifiedResearchProvenanceRecord(project_entity_id=project_id,provenance_key=p["provenance_key"],activity_type=p["activity_type"],source_refs_json=p.get("source_refs",[]),input_refs_json=p.get("input_refs",[]),output_refs_json=p.get("output_refs",[]),method_ref=p.get("method_ref"),runtime_json=p.get("runtime",{}),transformation_json=p.get("transformation",{}),recorded_by=p.get("recorded_by","operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def handoff(db:Session,project_id:str,p:dict):
    _reject(p); _profile(db,project_id); target=p["target_product"]
    if target not in PRODUCTS: raise ValueError("unsupported Catalyst product: "+target)
    row=UnifiedResearchRuntimeHandoffRecord(project_entity_id=project_id,handoff_key=p["handoff_key"],target_product=target,capability=p["capability"],request_contract_json=p.get("request_contract",{}),result_refs_json=p.get("result_refs",[]),status=p.get("status","declared"),provenance_json=p.get("provenance",{})); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def bundle(db:Session,project_id:str,public_only:bool=False):
    ent,base=_base(db,project_id); profile=_profile(db,project_id)
    if public_only and (ent.visibility!="public" or profile.visibility!="public"): raise ValueError("unified research project is not public.")
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.project_entity_id==project_id)).all()]
    return {"contract":CONTRACT,"project":{"entity_id":project_id,"name":ent.name,"description":ent.description,"visibility":ent.visibility,"base_profile":_ser(base),"unified_profile":_ser(profile)},"questions":rows(UnifiedResearchQuestionRecord),"objectives":rows(UnifiedResearchObjectiveRecord),"components":rows(UnifiedResearchComponentRecord),"relationships":rows(UnifiedResearchRelationshipRecord),"provenance_records":rows(UnifiedResearchProvenanceRecord),"handoffs":rows(UnifiedResearchRuntimeHandoffRecord),"snapshots":rows(UnifiedResearchProjectSnapshotRecord),"boundaries":boundaries()}

def snapshot(db:Session,project_id:str,p:dict):
    _reject(p); state=bundle(db,project_id); state.pop("snapshots",None)
    prev=db.scalars(select(UnifiedResearchProjectSnapshotRecord).where(UnifiedResearchProjectSnapshotRecord.project_entity_id==project_id).order_by(UnifiedResearchProjectSnapshotRecord.revision.asc())).all(); rev=len(prev)+1; ph=prev[-1].content_hash if prev else None; ch=_hash({"revision":rev,"previous_snapshot_hash":ph,"state":state})
    row=UnifiedResearchProjectSnapshotRecord(project_entity_id=project_id,revision=rev,content_hash=ch,previous_snapshot_hash=ph,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)
