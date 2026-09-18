from __future__ import annotations
import hashlib, json
from collections import deque
from datetime import datetime
from sqlalchemy import func, select, inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    UnifiedResearchProjectProfileRecord,
    ResearchLineageGraphRecord, ResearchLineageNodeRecord, ResearchLineageEdgeRecord,
    ResearchLineageActivityRecord, ResearchLineageTransformationRecord,
    ResearchLineageSourceBindingRecord, ResearchLineageTraceRecord, ResearchLineageSnapshotRecord,
)

CONTRACT = "sc.research.lineage-graph.v1"
NODE_TYPES = {
    "source", "literature", "source_collection", "dataset", "transformation", "methodology",
    "model", "analysis_run", "result", "finding", "evidence", "visualization", "investigation",
    "conclusion", "limitation", "external_artifact",
}
PREDICATES = {
    "derived_from", "produced_by", "used_input", "executed_with", "transformed_from",
    "supported_by", "interpreted_from", "discussed_against", "visualizes", "cites",
    "version_of", "validated_by", "bound_to",
}
ACTIVITY_TYPES = {"ingest", "transform", "analyze", "model", "simulate", "visualize", "interpret", "review", "publish", "external"}
PRODUCTS = {"library", "lab", "workbench", "decision-studio", "site-intelligence", "workspace", "research-librarian", "platform-core", "external"}
FORBIDDEN = {
    "infer_missing_edges_by_core", "infer_causality_by_core", "generate_findings_by_core",
    "promote_truth_by_core", "infer_originality_by_core", "execute_analysis_by_core",
    "alter_source_evidence_by_core",
}

def _ser(row):
    out = {}
    for a in sa_inspect(row).mapper.column_attrs:
        v = getattr(row, a.key)
        out[a.key] = v.isoformat() if isinstance(v, datetime) else v
    for k in list(out):
        if k.endswith("_json"):
            out[k[:-5]] = out.pop(k)
    return out

def _hash(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

def _reject(p):
    bad = sorted(k for k in FORBIDDEN if p.get(k) not in (None, False))
    if bad:
        raise ValueError("Research lineage is declarative; Core does not execute or infer: " + ", ".join(bad))

def boundaries():
    return {
        "lineage_graph_registry_by_core": True,
        "lineage_node_registry_by_core": True,
        "explicit_lineage_edge_registry_by_core": True,
        "provenance_activity_registry_by_core": True,
        "transformation_registry_by_core": True,
        "source_binding_registry_by_core": True,
        "deterministic_declared_trace_by_core": True,
        "immutable_lineage_snapshots_by_core": True,
        "infer_missing_edges_by_core": False,
        "infer_causality_by_core": False,
        "generate_findings_by_core": False,
        "promote_truth_by_core": False,
        "infer_originality_by_core": False,
        "execute_analysis_by_core": False,
        "alter_source_evidence_by_core": False,
    }

CLASSES = [ResearchLineageGraphRecord, ResearchLineageNodeRecord, ResearchLineageEdgeRecord, ResearchLineageActivityRecord, ResearchLineageTransformationRecord, ResearchLineageSourceBindingRecord, ResearchLineageTraceRecord, ResearchLineageSnapshotRecord]
NAMES = ["graphs", "nodes", "edges", "activities", "transformations", "source_bindings", "traces", "snapshots"]

def readiness(db: Session):
    c = lambda cls: int(db.scalar(select(func.count()).select_from(cls)) or 0)
    return {
        "release": "2.73.0", "contract": CONTRACT,
        "node_types": sorted(NODE_TYPES), "predicates": sorted(PREDICATES), "activity_types": sorted(ACTIVITY_TYPES),
        "counts": dict(zip(NAMES, [c(x) for x in CLASSES])), **boundaries(),
    }

def _project(db: Session, project_id: str):
    row = db.get(UnifiedResearchProjectProfileRecord, project_id)
    if row is None:
        raise ValueError("project_entity_id must reference a v2.72 unified research project profile.")
    return row

def _graph(db: Session, graph_id: str):
    row = db.get(ResearchLineageGraphRecord, graph_id)
    if row is None:
        raise ValueError("research lineage graph not found.")
    return row

def _node(db: Session, graph_id: str, node_id: str):
    row = db.get(ResearchLineageNodeRecord, node_id)
    if row is None or row.graph_id != graph_id:
        raise ValueError("lineage node must belong to this graph.")
    return row

def create_graph(db: Session, project_id: str, p: dict):
    _reject(p); _project(db, project_id)
    title = str(p.get("title") or "").strip()
    if not title: raise ValueError("title is required.")
    row = ResearchLineageGraphRecord(project_entity_id=project_id, graph_key=p["graph_key"], title=title, purpose=p.get("purpose"), status=p.get("status", "active"), root_refs_json=p.get("root_refs", []), provenance_json=p.get("provenance", {}), metadata_json=p.get("metadata", {}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_node(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db, graph_id); typ=p["node_type"]
    if typ not in NODE_TYPES: raise ValueError("unsupported lineage node type: " + typ)
    product=p.get("product_key")
    if product and product not in PRODUCTS: raise ValueError("unsupported Catalyst product: " + product)
    row=ResearchLineageNodeRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,node_key=p["node_key"],node_type=typ,label=p["label"],canonical_ref=p.get("canonical_ref"),product_key=product,product_ref=p.get("product_ref"),version_ref=p.get("version_ref"),content_hash=p.get("content_hash"),attributes_json=p.get("attributes",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_edge(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db, graph_id); pred=p["predicate"]
    if pred not in PREDICATES: raise ValueError("unsupported lineage predicate: " + pred)
    a=_node(db,graph_id,p["source_node_id"]); b=_node(db,graph_id,p["target_node_id"])
    if a.id==b.id: raise ValueError("lineage edge cannot self-reference.")
    row=ResearchLineageEdgeRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,edge_key=p["edge_key"],source_node_id=a.id,predicate=pred,target_node_id=b.id,evidence_refs_json=p.get("evidence_refs",[]),method_ref=p.get("method_ref"),transformation_ref=p.get("transformation_ref"),uncertainty_json=p.get("uncertainty",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def _validate_node_ids(db,graph_id,ids):
    for node_id in ids: _node(db,graph_id,node_id)

def add_activity(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db,graph_id); typ=p["activity_type"]
    if typ not in ACTIVITY_TYPES: raise ValueError("unsupported lineage activity type: "+typ)
    product=p.get("product_key")
    if product and product not in PRODUCTS: raise ValueError("unsupported Catalyst product: "+product)
    ins=p.get("input_node_ids",[]); outs=p.get("output_node_ids",[]); _validate_node_ids(db,graph_id,ins+outs)
    row=ResearchLineageActivityRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,activity_key=p["activity_key"],activity_type=typ,product_key=product,actor_ref=p.get("actor_ref"),method_ref=p.get("method_ref"),input_node_ids_json=ins,output_node_ids_json=outs,parameter_refs_json=p.get("parameter_refs",[]),environment_json=p.get("environment",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_transformation(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db,graph_id); a=_node(db,graph_id,p["source_node_id"]); b=_node(db,graph_id,p["output_node_id"])
    row=ResearchLineageTransformationRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,transformation_key=p["transformation_key"],source_node_id=a.id,output_node_id=b.id,operation=p["operation"],method_ref=p.get("method_ref"),code_ref=p.get("code_ref"),parameters_json=p.get("parameters",{}),environment_json=p.get("environment",{}),integrity_json=p.get("integrity",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_source_binding(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db,graph_id); n=_node(db,graph_id,p["node_id"])
    row=ResearchLineageSourceBindingRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,binding_key=p["binding_key"],node_id=n.id,source_ref=p["source_ref"],source_kind=p.get("source_kind","source"),source_version=p.get("source_version"),retrieval_ref=p.get("retrieval_ref"),citation_ref=p.get("citation_ref"),content_hash=p.get("content_hash"),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def _trace_path(db: Session, graph_id: str, start: str, end: str, orientation: str):
    _node(db,graph_id,start); _node(db,graph_id,end)
    if orientation not in {"outbound","inbound","both"}: raise ValueError("orientation must be outbound, inbound, or both.")
    edges=list(db.scalars(select(ResearchLineageEdgeRecord).where(ResearchLineageEdgeRecord.graph_id==graph_id)).all())
    adj={}
    for e in edges:
        if orientation in {"outbound","both"}: adj.setdefault(e.source_node_id,[]).append((e.target_node_id,e.id))
        if orientation in {"inbound","both"}: adj.setdefault(e.target_node_id,[]).append((e.source_node_id,e.id))
    q=deque([(start,[start],[])]); seen={start}
    while q:
        cur,nodes,eids=q.popleft()
        if cur==end: return nodes,eids
        for nxt,eid in adj.get(cur,[]):
            if nxt not in seen:
                seen.add(nxt); q.append((nxt,nodes+[nxt],eids+[eid]))
    raise ValueError("no declared lineage path connects the requested nodes.")

def create_trace(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db,graph_id); orientation=p.get("orientation","outbound")
    nodes,edges=_trace_path(db,graph_id,p["start_node_id"],p["end_node_id"],orientation)
    trace_state={"graph_id":graph_id,"start_node_id":p["start_node_id"],"end_node_id":p["end_node_id"],"orientation":orientation,"path_node_ids":nodes,"path_edge_ids":edges}
    row=ResearchLineageTraceRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,trace_key=p["trace_key"],start_node_id=p["start_node_id"],end_node_id=p["end_node_id"],orientation=orientation,path_node_ids_json=nodes,path_edge_ids_json=edges,purpose=p.get("purpose"),trace_hash=_hash(trace_state),provenance_json=p.get("provenance",{}))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)

def bundle(db: Session, graph_id: str, public_only: bool=False):
    g=_graph(db,graph_id); profile=_project(db,g.project_entity_id)
    if public_only and profile.visibility != "public": raise ValueError("research project is not public.")
    def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.graph_id==graph_id)).all()]
    return {"contract":CONTRACT,"graph":_ser(g),"project":{"project_entity_id":profile.project_entity_id,"project_key":profile.project_key,"title":profile.title,"visibility":profile.visibility},"nodes":rows(ResearchLineageNodeRecord),"edges":rows(ResearchLineageEdgeRecord),"activities":rows(ResearchLineageActivityRecord),"transformations":rows(ResearchLineageTransformationRecord),"source_bindings":rows(ResearchLineageSourceBindingRecord),"traces":rows(ResearchLineageTraceRecord),"snapshots":rows(ResearchLineageSnapshotRecord),"boundaries":boundaries()}

def snapshot(db: Session, graph_id: str, p: dict):
    _reject(p); g=_graph(db,graph_id); state=bundle(db,graph_id); state.pop("snapshots",None)
    last=db.scalar(select(ResearchLineageSnapshotRecord).where(ResearchLineageSnapshotRecord.graph_id==graph_id).order_by(ResearchLineageSnapshotRecord.revision.desc()).limit(1))
    revision=(last.revision+1) if last else 1; digest=_hash(state)
    row=ResearchLineageSnapshotRecord(graph_id=graph_id,project_entity_id=g.project_entity_id,revision=revision,content_hash=digest,previous_snapshot_hash=last.content_hash if last else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator"))
    db.add(row); db.commit(); db.refresh(row); return _ser(row)
