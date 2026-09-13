from __future__ import annotations
from collections import defaultdict, deque
from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import Entity, ResearchModelRecord, ResearchModelVersionRecord, CausalGraphRecord, CausalVariableRecord, CausalEdgeRecord, CausalInterventionRecord, CausalIdentificationRecord, CausalEstimateRecord, CausalDiagnosticRecord

ROLES={"variable","treatment","outcome","confounder","mediator","instrument","collider","selection","latent","context"}
EDGE_KINDS={"causal","structural","temporal","policy","association"}
SIGNS={"positive","negative","mixed","unknown"}
ID_METHODS={"unassessed","backdoor","frontdoor","instrumental-variable","difference-in-differences","regression-discontinuity","matching","weighting","g-formula","structural-equation","bayesian","custom"}
ID_STATUSES={"unassessed","candidate","identified","not-identified","disputed"}


def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,'isoformat'): v=v.isoformat()
        out[c.name]=v
    return out

def _graph(db:Session,gid:str)->CausalGraphRecord:
    row=db.get(CausalGraphRecord,gid)
    if row is None: raise HTTPException(status_code=404,detail='Causal graph not found.')
    return row

def _var(db:Session,gid:str,vid:str)->CausalVariableRecord:
    row=db.get(CausalVariableRecord,vid)
    if row is None or row.graph_id!=gid: raise ValueError('Variable must belong to this causal graph.')
    return row

def readiness(db:Session)->dict[str,Any]:
    counts={
      'graphs':db.scalar(select(func.count()).select_from(CausalGraphRecord)) or 0,
      'variables':db.scalar(select(func.count()).select_from(CausalVariableRecord)) or 0,
      'edges':db.scalar(select(func.count()).select_from(CausalEdgeRecord)) or 0,
      'interventions':db.scalar(select(func.count()).select_from(CausalInterventionRecord)) or 0,
      'identifications':db.scalar(select(func.count()).select_from(CausalIdentificationRecord)) or 0,
      'estimates':db.scalar(select(func.count()).select_from(CausalEstimateRecord)) or 0,
      'diagnostics':db.scalar(select(func.count()).select_from(CausalDiagnosticRecord)) or 0,
    }
    return {'counts':counts,'migration_0041_applied':True,'visual_kind':'causal-map','dag_validation_by_core':True,'path_reasoning_by_core':True,'adjustment_candidates_by_core':True,'automatic_causal_identification':False,'automatic_effect_estimation':False,'arbitrary_model_execution_by_core':False,'automatic_truth_promotion':False}

def create_graph(db:Session,p:dict[str,Any])->dict[str,Any]:
    pid=str(p.get('project_entity_id') or '')
    e=db.get(Entity,pid)
    if e is None or e.entity_type!='research-project': raise ValueError('project_entity_id must reference a research-project.')
    mid=p.get('model_entity_id'); mvid=p.get('model_version_entity_id')
    if mid:
        m=db.get(ResearchModelRecord,mid)
        if m is None or (m.project_entity_id and m.project_entity_id!=pid): raise ValueError('model_entity_id must reference a model in this project.')
    if mvid:
        mv=db.get(ResearchModelVersionRecord,mvid)
        if mv is None or (mid and mv.model_entity_id!=mid): raise ValueError('model_version_entity_id must reference a version of model_entity_id.')
    row=CausalGraphRecord(graph_key=str(p.get('graph_key') or 'causal-system'),name=str(p.get('name') or 'Causal system'),description=p.get('description'),visibility=str(p.get('visibility') or 'private'),project_entity_id=pid,model_entity_id=mid,model_version_entity_id=mvid,visual_entity_id=p.get('visual_entity_id'),graph_state=str(p.get('graph_state') or 'draft'),causal_semantics=str(p.get('causal_semantics') or 'directed-acyclic'),assumptions_json=list(p.get('assumptions') or []),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}),created_by=str(p.get('created_by') or 'operator'))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail='Causal graph key already exists in this project.') from exc
    return _ser(row)

def list_graphs(db:Session,*,public_only=False,limit=100,offset=0):
    q=select(CausalGraphRecord); cq=select(func.count()).select_from(CausalGraphRecord)
    if public_only: q=q.where(CausalGraphRecord.visibility=='public'); cq=cq.where(CausalGraphRecord.visibility=='public')
    total=int(db.scalar(cq) or 0); rows=db.scalars(q.order_by(CausalGraphRecord.created_at.desc()).limit(limit).offset(offset)).all(); return [_ser(x) for x in rows],total

def read_graph(db:Session,gid:str,*,public_only=False):
    row=_graph(db,gid)
    if public_only and row.visibility!='public': raise HTTPException(status_code=404,detail='Causal graph not found.')
    return _ser(row)

def add_variable(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); role=str(p.get('causal_role') or 'variable')
    if role not in ROLES: raise ValueError('Unsupported causal_role.')
    bound=p.get('bound_entity_id')
    if bound and db.get(Entity,bound) is None: raise ValueError('bound_entity_id must reference an existing Core entity.')
    row=CausalVariableRecord(graph_id=gid,variable_key=str(p.get('variable_key') or role),label=str(p.get('label') or p.get('variable_key') or role),causal_role=role,bound_entity_id=bound,observed=bool(p.get('observed',True)),unit=p.get('unit'),temporal_index_json=dict(p.get('temporal_index') or {}),uncertainty_json=dict(p.get('uncertainty') or {}),metadata_json=dict(p.get('metadata') or {})); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail='Causal variable key already exists.') from exc
    return _ser(row)

def add_edge(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); src=_var(db,gid,str(p.get('source_variable_id') or '')); dst=_var(db,gid,str(p.get('target_variable_id') or ''))
    if src.id==dst.id: raise ValueError('Self-causal edges are not permitted.')
    kind=str(p.get('edge_kind') or 'causal'); sign=str(p.get('sign') or 'unknown')
    if kind not in EDGE_KINDS: raise ValueError('Unsupported edge_kind.')
    if sign not in SIGNS: raise ValueError('Unsupported sign.')
    conf=p.get('confidence')
    if conf is not None and not 0<=float(conf)<=1: raise ValueError('confidence must be between 0 and 1.')
    row=CausalEdgeRecord(graph_id=gid,source_variable_id=src.id,target_variable_id=dst.id,edge_kind=kind,sign=sign,lag_json=dict(p.get('lag') or {}),confidence=float(conf) if conf is not None else None,assumptions_json=list(p.get('assumptions') or []),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {})); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail='Causal edge already exists.') from exc
    return _ser(row)

def _network(db:Session,gid:str):
    vars=db.scalars(select(CausalVariableRecord).where(CausalVariableRecord.graph_id==gid)).all(); edges=db.scalars(select(CausalEdgeRecord).where(CausalEdgeRecord.graph_id==gid,CausalEdgeRecord.edge_kind.in_(['causal','structural','temporal','policy']))).all()
    ids={v.id for v in vars}; adj={i:[] for i in ids}; rev={i:[] for i in ids}
    for e in edges:
        if e.source_variable_id in ids and e.target_variable_id in ids:
            adj[e.source_variable_id].append(e.target_variable_id); rev[e.target_variable_id].append(e.source_variable_id)
    return vars,edges,adj,rev

def _closure(start:str,adj:dict[str,list[str]])->set[str]:
    seen=set(); q=deque([start])
    while q:
        n=q.popleft()
        for x in adj.get(n,[]):
            if x not in seen and x!=start: seen.add(x); q.append(x)
    return seen

def validate_graph(db:Session,gid:str):
    _graph(db,gid); vars,edges,adj,rev=_network(db,gid); indeg={v.id:0 for v in vars}
    for e in edges: indeg[e.target_variable_id]=indeg.get(e.target_variable_id,0)+1
    q=deque(sorted([k for k,v in indeg.items() if v==0])); order=[]
    while q:
        n=q.popleft(); order.append(n)
        for x in adj.get(n,[]):
            indeg[x]-=1
            if indeg[x]==0:q.append(x)
    is_dag=len(order)==len(vars); cyclic=sorted(set(indeg)-set(order)) if not is_dag else []
    return {'graph_id':gid,'variable_count':len(vars),'directed_edge_count':len(edges),'is_dag':is_dag,'topological_order':order if is_dag else [],'cycle_member_candidates':cyclic,'structurally_valid':is_dag,'causal_identification_performed':False,'effect_estimation_performed':False}

def paths(db:Session,gid:str,source_id:str,target_id:str,max_paths=50):
    _var(db,gid,source_id); _var(db,gid,target_id); _,_,adj,_=_network(db,gid); out=[]
    def walk(n,path):
        if len(out)>=max_paths:return
        if n==target_id:out.append(path[:]);return
        for x in adj.get(n,[]):
            if x not in path:walk(x,path+[x])
    walk(source_id,[source_id]); return {'source_variable_id':source_id,'target_variable_id':target_id,'directed_paths':out,'path_count':len(out),'truncated':len(out)>=max_paths}

def adjustment_candidates(db:Session,gid:str,treatment_id:str,outcome_id:str):
    t=_var(db,gid,treatment_id); o=_var(db,gid,outcome_id); vars,edges,adj,rev=_network(db,gid)
    ancestors_out=_closure(outcome_id,rev); descendants_t=_closure(treatment_id,adj); parents_t=set(rev.get(treatment_id,[]))
    candidates=sorted(x for x in parents_t if x in ancestors_out and x not in descendants_t and x!=outcome_id)
    observed={v.id:v.observed for v in vars}; observed_candidates=[x for x in candidates if observed.get(x,False)]
    return {'treatment_variable_id':t.id,'outcome_variable_id':o.id,'candidate_adjustment_set':observed_candidates,'candidate_only':True,'identification_claimed':False,'note':'Conservative structural candidate set based on observed parents of treatment that are ancestors of outcome; analyst/method-specific identification is still required.'}

def add_intervention(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); v=_var(db,gid,str(p.get('variable_id') or ''))
    row=CausalInterventionRecord(graph_id=gid,variable_id=v.id,intervention_kind=str(p.get('intervention_kind') or 'set'),value_json=p.get('value'),comparison_value_json=p.get('comparison_value'),unit=p.get('unit'),assumptions_json=list(p.get('assumptions') or []),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}),created_by=str(p.get('created_by') or 'operator')); db.add(row); db.commit(); db.refresh(row); return _ser(row)

def add_identification(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); t=_var(db,gid,str(p.get('treatment_variable_id') or '')); o=_var(db,gid,str(p.get('outcome_variable_id') or ''))
    method=str(p.get('identification_method') or 'unassessed'); status=str(p.get('identification_status') or 'unassessed')
    if method not in ID_METHODS: raise ValueError('Unsupported identification_method.')
    if status not in ID_STATUSES: raise ValueError('Unsupported identification_status.')
    adj=list(p.get('adjustment_set') or [])
    for x in adj:_var(db,gid,str(x))
    if status=='identified' and not list(p.get('assumptions') or []): raise ValueError('Identified claims require explicit assumptions.')
    row=CausalIdentificationRecord(graph_id=gid,treatment_variable_id=t.id,outcome_variable_id=o.id,estimand=str(p.get('estimand') or 'ATE'),identification_method=method,identification_status=status,adjustment_set_json=adj,assumptions_json=list(p.get('assumptions') or []),rationale_json=dict(p.get('rationale') or {}),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}),created_by=str(p.get('created_by') or 'operator'));db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_estimate(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); iid=p.get('identification_id')
    if iid:
        ident=db.get(CausalIdentificationRecord,iid)
        if ident is None or ident.graph_id!=gid: raise ValueError('identification_id must belong to this graph.')
    source=dict(p.get('source_execution') or {}); prov=dict(p.get('provenance') or {})
    if not source and not prov: raise ValueError('Causal estimates require source_execution or provenance.')
    conf=p.get('confidence_level')
    if conf is not None and not 0<float(conf)<=1: raise ValueError('confidence_level must be in (0,1].')
    row=CausalEstimateRecord(graph_id=gid,identification_id=iid,estimate_kind=str(p.get('estimate_kind') or 'effect'),estimate_value=float(p.get('estimate_value')),lower_bound=float(p['lower_bound']) if p.get('lower_bound') is not None else None,upper_bound=float(p['upper_bound']) if p.get('upper_bound') is not None else None,confidence_level=float(conf) if conf is not None else None,unit=p.get('unit'),method=str(p.get('method') or 'external'),source_execution_json=source,provenance_json=prov,metadata_json=dict(p.get('metadata') or {}));db.add(row);db.commit();db.refresh(row);return _ser(row)

def add_diagnostic(db:Session,gid:str,p:dict[str,Any]):
    _graph(db,gid); iid=p.get('identification_id')
    if iid:
        ident=db.get(CausalIdentificationRecord,iid)
        if ident is None or ident.graph_id!=gid: raise ValueError('identification_id must belong to this graph.')
    row=CausalDiagnosticRecord(graph_id=gid,identification_id=iid,diagnostic_kind=str(p.get('diagnostic_kind') or 'diagnostic'),status=str(p.get('status') or 'reported'),value_json=p.get('value'),threshold_json=p.get('threshold'),interpretation=p.get('interpretation'),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}));db.add(row);db.commit();db.refresh(row);return _ser(row)

def runtime_handoff(db:Session,gid:str,p:dict[str,Any]):
    g=_graph(db,gid); target=str(p.get('target_product') or 'lab')
    if target not in {'lab','workbench','external'}: raise ValueError('target_product must be lab, workbench, or external.')
    if p.get('execute_by_core') is True: raise ValueError('Platform Core does not execute arbitrary causal estimation models.')
    return {'contract':'sc.causal-estimation-handoff.v1','graph_id':gid,'project_entity_id':g.project_entity_id,'model_entity_id':g.model_entity_id,'target_product':target,'method':str(p.get('method') or 'custom'),'estimand':str(p.get('estimand') or 'ATE'),'treatment_variable_id':p.get('treatment_variable_id'),'outcome_variable_id':p.get('outcome_variable_id'),'adjustment_set':list(p.get('adjustment_set') or []),'assumptions':list(p.get('assumptions') or []),'input_manifest':dict(p.get('input_manifest') or {}),'model_execution_by_core':False,'automatic_truth_promotion':False}

def bundle(db:Session,gid:str,*,public_only=False):
    graph=read_graph(db,gid,public_only=public_only)
    vars=db.scalars(select(CausalVariableRecord).where(CausalVariableRecord.graph_id==gid)).all(); edges=db.scalars(select(CausalEdgeRecord).where(CausalEdgeRecord.graph_id==gid)).all(); ints=db.scalars(select(CausalInterventionRecord).where(CausalInterventionRecord.graph_id==gid)).all(); ids=db.scalars(select(CausalIdentificationRecord).where(CausalIdentificationRecord.graph_id==gid)).all(); est=db.scalars(select(CausalEstimateRecord).where(CausalEstimateRecord.graph_id==gid)).all(); diag=db.scalars(select(CausalDiagnosticRecord).where(CausalDiagnosticRecord.graph_id==gid)).all()
    return {'graph':graph,'variables':[_ser(x) for x in vars],'edges':[_ser(x) for x in edges],'interventions':[_ser(x) for x in ints],'identifications':[_ser(x) for x in ids],'estimates':[_ser(x) for x in est],'diagnostics':[_ser(x) for x in diag],'validation':validate_graph(db,gid),'visualization':{'visual_kind':'causal-map','renderer_contract':'contract.d3','renderer_execution_by_core':False,'layout_execution_by_core':False}}
