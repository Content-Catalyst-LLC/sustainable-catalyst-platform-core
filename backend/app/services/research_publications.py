from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json

from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..models import (
    UnifiedResearchProjectProfileRecord, ResearchConclusionRecord,
    ResearchPublicationRecord, ResearchPublicationSectionRecord, ResearchPublicationReferenceRecord,
    ResearchPublicationCitationRecord, ResearchPublicationFigureRecord, ResearchPublicationSupplementRecord,
    ResearchPublicationIdentifierRecord, ResearchPublicationExportRecord, ResearchPublicationRevisionRecord,
    ResearchPublicationSnapshotRecord,
)

CONTRACT = "sc.research.reproducible-publication.v1"
PUBLICATION_TYPES = {"paper","technical_report","research_brief","working_paper","investigation_report","thesis_chapter","dataset_note","methodological_note"}
PUBLICATION_STATUSES = {"draft","in_review","revised","accepted","published_external","superseded","withdrawn","archived"}
SECTION_TYPES = {"abstract","introduction","background","literature_review","methods","results","findings","discussion","limitations","conclusion","references","appendix","supplement_note","other"}
REFERENCE_TYPES = {"source","article","book","chapter","dataset","software","report","web","standard","legal","other"}
FIGURE_TYPES = {"figure","table","map","chart","diagram","model","visualization","image","other"}
SUPPLEMENT_TYPES = {"dataset","notebook","code","model","visualization","evidence_package","methods_appendix","reproducibility_package","other"}
IDENTIFIER_TYPES = {"doi","handle","ark","isbn","issn","url","repository_id","external_id","other"}
EXPORT_FORMATS = {"markdown","json","html","pdf","docx"}
FORBIDDEN = {"generate_manuscript_by_core","generate_conclusion_by_core","fabricate_citation_by_core","judge_publication_quality_by_core","certify_publication_by_core","issue_doi_by_core","publish_external_by_core","infer_truth_by_core"}
CLASSES=[ResearchPublicationRecord,ResearchPublicationSectionRecord,ResearchPublicationReferenceRecord,ResearchPublicationCitationRecord,ResearchPublicationFigureRecord,ResearchPublicationSupplementRecord,ResearchPublicationIdentifierRecord,ResearchPublicationExportRecord,ResearchPublicationRevisionRecord,ResearchPublicationSnapshotRecord]
COUNT_NAMES=["publications","sections","references","citations","figures","supplements","identifiers","exports","revisions","snapshots"]

def _ser(record):
    out={}
    for attr in sa_inspect(record).mapper.column_attrs:
        value=getattr(record,attr.key); out[attr.key]=value.isoformat() if isinstance(value,datetime) else value
    for key in list(out):
        if key.endswith("_json"): out[key[:-5]]=out.pop(key)
    return out

def _hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _reject(payload):
    bad=sorted(k for k in FORBIDDEN if payload.get(k) not in (None,False))
    if bad: raise ValueError("Publication Core preserves researcher-authored scholarly records; it does not author conclusions, fabricate citations, judge/certify quality, issue identifiers, infer truth, or publish externally: "+", ".join(bad))

def boundaries():
    return {"structured_publication_registry_by_core":True,"manuscript_section_registry_by_core":True,"bibliographic_reference_registry_by_core":True,"claim_citation_traceability_by_core":True,"figure_table_registry_by_core":True,"supplement_manifest_by_core":True,"external_identifier_registry_by_core":True,"structural_readiness_diagnostics_by_core":True,"research_to_publication_lineage_by_core":True,"export_manifest_registry_by_core":True,"publication_revision_history_by_core":True,"immutable_publication_snapshots_by_core":True,"generate_manuscript_by_core":False,"generate_conclusion_by_core":False,"fabricate_citation_by_core":False,"judge_publication_quality_by_core":False,"certify_publication_by_core":False,"issue_doi_by_core":False,"publish_external_by_core":False,"infer_truth_by_core":False}

def readiness(db):
    count=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {"release":"2.81.0","contract":CONTRACT,"publication_types":sorted(PUBLICATION_TYPES),"publication_statuses":sorted(PUBLICATION_STATUSES),"section_types":sorted(SECTION_TYPES),"reference_types":sorted(REFERENCE_TYPES),"figure_types":sorted(FIGURE_TYPES),"supplement_types":sorted(SUPPLEMENT_TYPES),"identifier_types":sorted(IDENTIFIER_TYPES),"export_formats":sorted(EXPORT_FORMATS),"counts":dict(zip(COUNT_NAMES,[count(c) for c in CLASSES])),**boundaries()}

def _project(db,pid):
    x=db.get(UnifiedResearchProjectProfileRecord,pid)
    if x is None: raise ValueError("project_entity_id must reference a v2.72 unified research project profile.")
    return x

def _publication(db,pub_id):
    x=db.get(ResearchPublicationRecord,pub_id)
    if x is None: raise ValueError("research publication not found.")
    return x

def create_publication(db,project_id,payload):
    _reject(payload); _project(db,project_id)
    key=str(payload.get("publication_key") or "").strip(); title=str(payload.get("title") or "").strip(); typ=payload.get("publication_type","working_paper"); status=payload.get("status","draft")
    if not key or not title: raise ValueError("publication_key and title are required.")
    if typ not in PUBLICATION_TYPES: raise ValueError("unsupported publication_type: "+str(typ))
    if status not in PUBLICATION_STATUSES: raise ValueError("unsupported publication status: "+str(status))
    conclusion_id=payload.get("conclusion_id")
    if conclusion_id is not None:
        c=db.get(ResearchConclusionRecord,conclusion_id)
        if c is None or c.project_entity_id!=project_id: raise ValueError("conclusion_id must reference a v2.80 conclusion in this project.")
    r=ResearchPublicationRecord(project_entity_id=project_id,conclusion_id=conclusion_id,publication_key=key,title=title,publication_type=typ,status=status,abstract_text=payload.get("abstract_text"),required_sections_json=payload.get("required_sections",[]),keywords_json=payload.get("keywords",[]),authors_json=payload.get("authors",[]),limitations_json=payload.get("limitations",[]),provenance_json=payload.get("provenance",{}),metadata_json=payload.get("metadata",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_section(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); typ=payload.get("section_type","other")
    if typ not in SECTION_TYPES: raise ValueError("unsupported section_type: "+str(typ))
    key=str(payload.get("section_key") or "").strip(); heading=str(payload.get("heading") or "").strip()
    if not key or not heading: raise ValueError("section_key and heading are required.")
    r=ResearchPublicationSectionRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,section_key=key,section_type=typ,heading=heading,section_index=int(payload.get("section_index",0)),body_text=str(payload.get("body_text") or ""),source_refs_json=payload.get("source_refs",[]),claim_refs_json=payload.get("claim_refs",[]),provenance_json=payload.get("provenance",{}),metadata_json=payload.get("metadata",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_reference(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); typ=payload.get("reference_type","source")
    if typ not in REFERENCE_TYPES: raise ValueError("unsupported reference_type: "+str(typ))
    key=str(payload.get("reference_key") or "").strip(); title=str(payload.get("title") or "").strip()
    if not key or not title: raise ValueError("reference_key and title are required.")
    r=ResearchPublicationReferenceRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,reference_key=key,reference_type=typ,title=title,authors_json=payload.get("authors",[]),issued_json=payload.get("issued",{}),doi=payload.get("doi"),url=payload.get("url"),source_ref=payload.get("source_ref"),citation_data_json=payload.get("citation_data",{}),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_citation(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); sec=db.get(ResearchPublicationSectionRecord,payload.get("section_id")); ref=db.get(ResearchPublicationReferenceRecord,payload.get("reference_id"))
    if sec is None or sec.publication_id!=pub_id: raise ValueError("section_id must reference a section in this publication.")
    if ref is None or ref.publication_id!=pub_id: raise ValueError("reference_id must reference a bibliographic reference in this publication.")
    key=str(payload.get("citation_key") or "").strip()
    if not key: raise ValueError("citation_key is required.")
    r=ResearchPublicationCitationRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,section_id=sec.id,reference_id=ref.id,citation_key=key,claim_ref=payload.get("claim_ref"),locator=payload.get("locator"),context_text=payload.get("context_text"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator"))
    db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_figure(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); typ=payload.get("figure_type","figure")
    if typ not in FIGURE_TYPES: raise ValueError("unsupported figure_type: "+str(typ))
    if not str(payload.get("figure_key") or "").strip() or not str(payload.get("title") or "").strip() or not str(payload.get("source_ref") or "").strip(): raise ValueError("figure_key, title, and source_ref are required.")
    r=ResearchPublicationFigureRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,figure_key=payload["figure_key"],figure_type=typ,title=payload["title"],caption_text=payload.get("caption_text"),source_ref=payload["source_ref"],artifact_ref=payload.get("artifact_ref"),version_ref=payload.get("version_ref"),provenance_json=payload.get("provenance",{}),metadata_json=payload.get("metadata",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_supplement(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); typ=payload.get("supplement_type")
    if typ not in SUPPLEMENT_TYPES: raise ValueError("unsupported supplement_type: "+str(typ))
    if not all(str(payload.get(k) or "").strip() for k in ("supplement_key","title","artifact_ref")): raise ValueError("supplement_key, title, and artifact_ref are required.")
    r=ResearchPublicationSupplementRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,supplement_key=payload["supplement_key"],supplement_type=typ,title=payload["title"],artifact_ref=payload["artifact_ref"],version_ref=payload.get("version_ref"),integrity_json=payload.get("integrity",{}),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def add_identifier(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); typ=payload.get("identifier_type")
    if typ not in IDENTIFIER_TYPES: raise ValueError("unsupported identifier_type: "+str(typ))
    val=str(payload.get("identifier_value") or "").strip()
    if not val: raise ValueError("identifier_value is required.")
    r=ResearchPublicationIdentifierRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,identifier_type=typ,identifier_value=val,authority=payload.get("authority"),url=payload.get("url"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def structural_readiness(db,pub_id,public=False):
    p=_publication(db,pub_id); project=_project(db,p.project_entity_id)
    if public and project.visibility!="public": raise ValueError("research project is not public.")
    sections=list(db.scalars(select(ResearchPublicationSectionRecord).where(ResearchPublicationSectionRecord.publication_id==pub_id)).all()); refs=list(db.scalars(select(ResearchPublicationReferenceRecord).where(ResearchPublicationReferenceRecord.publication_id==pub_id)).all()); citations=list(db.scalars(select(ResearchPublicationCitationRecord).where(ResearchPublicationCitationRecord.publication_id==pub_id)).all()); figs=list(db.scalars(select(ResearchPublicationFigureRecord).where(ResearchPublicationFigureRecord.publication_id==pub_id)).all()); supp=list(db.scalars(select(ResearchPublicationSupplementRecord).where(ResearchPublicationSupplementRecord.publication_id==pub_id)).all())
    present={s.section_type for s in sections}; required=set(p.required_sections_json or []); missing=sorted(required-present)
    claim_refs=sorted({x for s in sections for x in (s.claim_refs_json or []) if x}); cited_claims={c.claim_ref for c in citations if c.claim_ref}; uncited=sorted(x for x in claim_refs if x not in cited_claims)
    return {"release":"2.81.0","contract":CONTRACT,"publication":_ser(p),"structural_readiness":{"required_sections":sorted(required),"present_section_types":sorted(present),"missing_required_sections":missing,"declared_claim_refs":claim_refs,"uncited_claim_refs":uncited,"reference_count":len(refs),"citation_count":len(citations),"figure_count":len(figs),"supplement_count":len(supp),"has_abstract":bool((p.abstract_text or "").strip())},"diagnostic_is_structural_only":True,"quality_score_computed":False,"publication_quality_judged":False,"external_publication_performed":False}

def lineage(db,pub_id,public=False):
    p=_publication(db,pub_id); project=_project(db,p.project_entity_id)
    if public and project.visibility!="public": raise ValueError("research project is not public.")
    c=db.get(ResearchConclusionRecord,p.conclusion_id) if p.conclusion_id else None
    sections=list(db.scalars(select(ResearchPublicationSectionRecord).where(ResearchPublicationSectionRecord.publication_id==pub_id).order_by(ResearchPublicationSectionRecord.section_index)).all())
    citations=list(db.scalars(select(ResearchPublicationCitationRecord).where(ResearchPublicationCitationRecord.publication_id==pub_id)).all())
    return {"release":"2.81.0","contract":CONTRACT,"project_ref":p.project_entity_id,"conclusion":None if c is None else _ser(c),"publication":_ser(p),"section_source_bindings":[{"section_id":s.id,"section_key":s.section_key,"source_refs":s.source_refs_json,"claim_refs":s.claim_refs_json} for s in sections],"citation_claim_bindings":[{"citation_id":x.id,"section_id":x.section_id,"reference_id":x.reference_id,"claim_ref":x.claim_ref} for x in citations],"lineage_is_declared_not_inferred":True,"missing_links_inferred_by_core":False}

def bundle(db,pub_id,public=False):
    p=_publication(db,pub_id); project=_project(db,p.project_entity_id)
    if public and project.visibility!="public": raise ValueError("research project is not public.")
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.publication_id==pub_id)).all()]
    return {"release":"2.81.0","contract":CONTRACT,"project":_ser(project),"publication":_ser(p),"sections":rows(ResearchPublicationSectionRecord),"references":rows(ResearchPublicationReferenceRecord),"citations":rows(ResearchPublicationCitationRecord),"figures":rows(ResearchPublicationFigureRecord),"supplements":rows(ResearchPublicationSupplementRecord),"identifiers":rows(ResearchPublicationIdentifierRecord),"exports":rows(ResearchPublicationExportRecord),"revisions":rows(ResearchPublicationRevisionRecord),"snapshots":rows(ResearchPublicationSnapshotRecord),"readiness":structural_readiness(db,pub_id,public),"lineage":lineage(db,pub_id,public),**boundaries()}

def create_export_manifest(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); key=str(payload.get("export_key") or "").strip(); formats=payload.get("formats",[])
    if not key: raise ValueError("export_key is required.")
    if not formats or any(f not in EXPORT_FORMATS for f in formats): raise ValueError("formats must contain supported export formats.")
    state=bundle(db,pub_id); state.pop("exports",None); state.pop("snapshots",None)
    manifest={"publication_id":pub_id,"formats":formats,"section_ids":[x["id"] for x in state["sections"]],"reference_ids":[x["id"] for x in state["references"]],"figure_ids":[x["id"] for x in state["figures"]],"supplement_ids":[x["id"] for x in state["supplements"]],"research_lineage_embedded":True,"generated_content":False,"external_renderer_required_for_pdf_docx":any(x in {"pdf","docx"} for x in formats)}
    h=_hash(manifest); r=ResearchPublicationExportRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,export_key=key,formats_json=formats,manifest_json=manifest,content_hash=h,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def revise_publication(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); prior=_ser(p)
    for fld in ("title","publication_type","status","abstract_text"):
        if fld in payload:
            if fld=="publication_type" and payload[fld] not in PUBLICATION_TYPES: raise ValueError("unsupported publication_type: "+str(payload[fld]))
            if fld=="status" and payload[fld] not in PUBLICATION_STATUSES: raise ValueError("unsupported publication status: "+str(payload[fld]))
            setattr(p,fld,payload[fld])
    for fld,attr in (("required_sections","required_sections_json"),("keywords","keywords_json"),("authors","authors_json"),("limitations","limitations_json"),("provenance","provenance_json"),("metadata","metadata_json")):
        if fld in payload: setattr(p,attr,payload[fld])
    n=db.scalar(select(func.max(ResearchPublicationRevisionRecord.revision)).where(ResearchPublicationRevisionRecord.publication_id==pub_id)) or 0; revised=_ser(p); h=_hash(revised)
    r=ResearchPublicationRevisionRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,revision=int(n)+1,state_hash=h,prior_state_json=prior,revised_state_json=revised,change_summary=payload.get("change_summary"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(p); db.add(r); db.commit(); db.refresh(r); return _ser(r)

def snapshot(db,pub_id,payload):
    _reject(payload); p=_publication(db,pub_id); state=bundle(db,pub_id); state.pop("snapshots",None); h=_hash(state); prev=db.scalar(select(ResearchPublicationSnapshotRecord).where(ResearchPublicationSnapshotRecord.publication_id==pub_id).order_by(ResearchPublicationSnapshotRecord.revision.desc()).limit(1)); rev=1 if prev is None else prev.revision+1
    r=ResearchPublicationSnapshotRecord(project_entity_id=p.project_entity_id,publication_id=pub_id,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
