from __future__ import annotations
import hashlib, json
from datetime import datetime
from sqlalchemy import func, select, inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (UnifiedResearchProjectProfileRecord, ResearchMethodologyRecord, ResearchMethodologyVersionRecord, ResearchMethodVariableRecord, ResearchMethodAssumptionRecord, ResearchMethodParameterRecord, ResearchExecutionEnvironmentRecord, ResearchAnalysisRunRecord, ResearchAnalysisRunInputRecord, ResearchAnalysisRunOutputRecord, ResearchMethodologySnapshotRecord)
CONTRACT='sc.research.methodology-analysis.v1'
PRODUCTS={'library','lab','workbench','decision-studio','site-intelligence','workspace','research-librarian','platform-core','external'}
METHOD_TYPES={'analytical','statistical','causal','experimental','simulation','modeling','spatial','qualitative','mixed-methods','external'}
VAR_ROLES={'independent','dependent','control','covariate','mediator','moderator','outcome','exposure','derived','other'}
ASSUMPTION_KINDS={'assumption','exclusion','limitation','constraint'}
FORBIDDEN={'execute_analysis_by_core','validate_results_by_core','infer_causality_by_core','judge_research_quality_by_core','infer_method_validity_by_core','select_method_by_core','alter_external_results_by_core'}
CLASSES=[ResearchMethodologyRecord,ResearchMethodologyVersionRecord,ResearchMethodVariableRecord,ResearchMethodAssumptionRecord,ResearchMethodParameterRecord,ResearchExecutionEnvironmentRecord,ResearchAnalysisRunRecord,ResearchAnalysisRunInputRecord,ResearchAnalysisRunOutputRecord,ResearchMethodologySnapshotRecord]
NAMES=['methodologies','versions','variables','assumptions','parameters','environments','runs','inputs','outputs','snapshots']
def _ser(r):
 out={}
 for a in sa_inspect(r).mapper.column_attrs:
  v=getattr(r,a.key); out[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(out):
  if k.endswith('_json'): out[k[:-5]]=out.pop(k)
 return out
def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad: raise ValueError('Methodology registry is declarative; Core does not execute or judge: '+', '.join(bad))
def boundaries():
 return {'methodology_registry_by_core':True,'methodology_version_registry_by_core':True,'variable_registry_by_core':True,'assumption_exclusion_registry_by_core':True,'parameter_registry_by_core':True,'execution_environment_registry_by_core':True,'analysis_run_registry_by_core':True,'run_input_output_registry_by_core':True,'immutable_methodology_snapshots_by_core':True,'execute_analysis_by_core':False,'validate_results_by_core':False,'infer_causality_by_core':False,'judge_research_quality_by_core':False,'infer_method_validity_by_core':False,'select_method_by_core':False,'alter_external_results_by_core':False}
def readiness(db):
 c=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
 return {'release':'2.74.0','contract':CONTRACT,'method_types':sorted(METHOD_TYPES),'variable_roles':sorted(VAR_ROLES),'assumption_kinds':sorted(ASSUMPTION_KINDS),'counts':dict(zip(NAMES,[c(x) for x in CLASSES])),**boundaries()}
def _project(db,pid):
 r=db.get(UnifiedResearchProjectProfileRecord,pid)
 if r is None: raise ValueError('project_entity_id must reference a v2.72 unified research project profile.')
 return r
def _method(db,mid):
 r=db.get(ResearchMethodologyRecord,mid)
 if r is None: raise ValueError('methodology not found.')
 return r
def _run(db,rid):
 r=db.get(ResearchAnalysisRunRecord,rid)
 if r is None: raise ValueError('analysis run not found.')
 return r
def create_methodology(db,pid,p):
 _reject(p); _project(db,pid); mt=p.get('method_type','analytical')
 if mt not in METHOD_TYPES: raise ValueError('unsupported method_type: '+mt)
 if not str(p.get('title') or '').strip(): raise ValueError('title is required.')
 r=ResearchMethodologyRecord(project_entity_id=pid,method_key=p['method_key'],title=p['title'],purpose=p.get('purpose'),method_type=mt,status=p.get('status','draft'),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{})); db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_version(db,mid,p):
 _reject(p); m=_method(db,mid); r=ResearchMethodologyVersionRecord(methodology_id=mid,project_entity_id=m.project_entity_id,version_key=p['version_key'],description=p.get('description'),protocol_json=p.get('protocol',{}),software_refs_json=p.get('software_refs',[]),code_refs_json=p.get('code_refs',[]),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_variable(db,mid,p):
 _reject(p); m=_method(db,mid); role=p['role']
 if role not in VAR_ROLES: raise ValueError('unsupported variable role: '+role)
 r=ResearchMethodVariableRecord(methodology_id=mid,project_entity_id=m.project_entity_id,variable_key=p['variable_key'],role=role,label=p['label'],unit=p.get('unit'),definition=p.get('definition'),source_ref=p.get('source_ref'),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_assumption(db,mid,p):
 _reject(p); m=_method(db,mid); kind=p.get('kind','assumption')
 if kind not in ASSUMPTION_KINDS: raise ValueError('unsupported assumption kind: '+kind)
 r=ResearchMethodAssumptionRecord(methodology_id=mid,project_entity_id=m.project_entity_id,assumption_key=p['assumption_key'],kind=kind,statement=p['statement'],rationale=p.get('rationale'),evidence_refs_json=p.get('evidence_refs',[]));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_parameter(db,mid,p):
 _reject(p); m=_method(db,mid); r=ResearchMethodParameterRecord(methodology_id=mid,project_entity_id=m.project_entity_id,parameter_key=p['parameter_key'],value_json=p.get('value',{}),unit=p.get('unit'),source_ref=p.get('source_ref'));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_environment(db,pid,p):
 _reject(p); _project(db,pid); product=p.get('product_key')
 if product and product not in PRODUCTS: raise ValueError('unsupported Catalyst product: '+product)
 r=ResearchExecutionEnvironmentRecord(project_entity_id=pid,environment_key=p['environment_key'],product_key=product,runtime=p.get('runtime'),runtime_version=p.get('runtime_version'),os_ref=p.get('os_ref'),package_manifest_json=p.get('package_manifest',{}),container_ref=p.get('container_ref'),hardware_json=p.get('hardware',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def create_run(db,pid,p):
 _reject(p); _project(db,pid); m=_method(db,p['methodology_id'])
 if m.project_entity_id!=pid: raise ValueError('methodology must belong to this project.')
 product=p.get('product_key')
 if product and product not in PRODUCTS: raise ValueError('unsupported Catalyst product: '+product)
 r=ResearchAnalysisRunRecord(project_entity_id=pid,run_key=p['run_key'],methodology_id=m.id,methodology_version_id=p.get('methodology_version_id'),environment_id=p.get('environment_id'),product_key=product,external_run_ref=p.get('external_run_ref'),status=p.get('status','declared'),parameters_json=p.get('parameters',{}),result_summary_json=p.get('result_summary',{}),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_input(db,rid,p):
 _reject(p); r0=_run(db,rid); r=ResearchAnalysisRunInputRecord(run_id=rid,project_entity_id=r0.project_entity_id,input_key=p['input_key'],input_type=p['input_type'],input_ref=p['input_ref'],version_ref=p.get('version_ref'),content_hash=p.get('content_hash'),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_output(db,rid,p):
 _reject(p); r0=_run(db,rid); r=ResearchAnalysisRunOutputRecord(run_id=rid,project_entity_id=r0.project_entity_id,output_key=p['output_key'],output_type=p['output_type'],output_ref=p['output_ref'],content_hash=p.get('content_hash'),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def bundle(db,pid,public=False):
 _project(db,pid)
 def rows(cls,field='project_entity_id'): return [_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field)==pid)).all()]
 methods=rows(ResearchMethodologyRecord); mids=[x['id'] for x in methods]; runs=rows(ResearchAnalysisRunRecord); rids=[x['id'] for x in runs]
 filt=lambda cls,field,vals:[_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field).in_(vals))).all()] if vals else []
 return {'release':'2.74.0','contract':CONTRACT,'project_entity_id':pid,'methodologies':methods,'versions':filt(ResearchMethodologyVersionRecord,'methodology_id',mids),'variables':filt(ResearchMethodVariableRecord,'methodology_id',mids),'assumptions':filt(ResearchMethodAssumptionRecord,'methodology_id',mids),'parameters':filt(ResearchMethodParameterRecord,'methodology_id',mids),'environments':rows(ResearchExecutionEnvironmentRecord),'runs':runs,'inputs':filt(ResearchAnalysisRunInputRecord,'run_id',rids),'outputs':filt(ResearchAnalysisRunOutputRecord,'run_id',rids),'snapshots':rows(ResearchMethodologySnapshotRecord),**boundaries()}
def snapshot(db,pid,p):
 _reject(p); state=bundle(db,pid); state.pop('snapshots',None); h=_hash(state); prev=db.scalar(select(ResearchMethodologySnapshotRecord).where(ResearchMethodologySnapshotRecord.project_entity_id==pid).order_by(ResearchMethodologySnapshotRecord.revision.desc()).limit(1)); rev=1 if prev is None else prev.revision+1
 r=ResearchMethodologySnapshotRecord(project_entity_id=pid,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)
