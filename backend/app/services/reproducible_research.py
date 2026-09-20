from datetime import datetime
import hashlib,json
from sqlalchemy import select,func,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (UnifiedResearchProjectProfileRecord,ResearchMethodologyRecord,ResearchMethodologyVersionRecord,ResearchAnalysisRunRecord,ResearchAnalysisRunInputRecord,ResearchAnalysisRunOutputRecord,ResearchExecutionEnvironmentRecord,ResearchLineageGraphRecord,ReproducibleResearchPackageRecord,ReproducibleResearchPackageComponentRecord,ReproducibleResearchPackageArtifactRecord,ReproducibleResearchPackageEnvironmentRecord,ReproducibleResearchReplayPlanRecord,ReproducibleResearchVerificationRecord,ReproducibleResearchReviewRecord,ReproducibleResearchSnapshotRecord)
CONTRACT='sc.research.reproducible-package.v1'
PRODUCTS={'library','lab','workbench','decision-studio','site-intelligence','workspace','research-librarian','platform-core','external'}
COMPONENT_TYPES={'project','question','objective','literature','source_collection','dataset','evidence','methodology','methodology_version','analysis_run','analysis_input','analysis_output','finding','visualization','investigation','lineage_graph','conclusion','limitation','other'}
FORBIDDEN={'execute_replay_by_core','reproduce_analysis_by_core','validate_finding_by_core','certify_scientific_truth_by_core','alter_artifacts_by_core','execute_handoff_by_core','infer_reproducibility_by_core'}
CLASSES=[ReproducibleResearchPackageRecord,ReproducibleResearchPackageComponentRecord,ReproducibleResearchPackageArtifactRecord,ReproducibleResearchPackageEnvironmentRecord,ReproducibleResearchReplayPlanRecord,ReproducibleResearchVerificationRecord,ReproducibleResearchReviewRecord,ReproducibleResearchSnapshotRecord]
NAMES=['packages','components','artifacts','environments','replay_plans','verifications','reviews','snapshots']
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
 if bad: raise ValueError('Reproducible research packages are declarative; Core does not execute or certify: '+', '.join(bad))
def boundaries():
 return {'package_registry_by_core':True,'component_manifest_by_core':True,'artifact_registry_by_core':True,'environment_capture_by_core':True,'replay_plan_registry_by_core':True,'verification_evidence_registry_by_core':True,'review_registry_by_core':True,'immutable_package_snapshots_by_core':True,'execute_replay_by_core':False,'reproduce_analysis_by_core':False,'validate_finding_by_core':False,'certify_scientific_truth_by_core':False,'alter_artifacts_by_core':False,'execute_handoff_by_core':False,'infer_reproducibility_by_core':False}
def readiness(db):
 c=lambda cls:int(db.scalar(select(func.count()).select_from(cls)) or 0)
 return {'release':'2.75.0','contract':CONTRACT,'component_types':sorted(COMPONENT_TYPES),'counts':dict(zip(NAMES,[c(x) for x in CLASSES])),**boundaries()}
def _project(db,pid):
 r=db.get(UnifiedResearchProjectProfileRecord,pid)
 if r is None: raise ValueError('project_entity_id must reference a v2.72 unified research project profile.')
 return r
def _package(db,pid):
 r=db.get(ReproducibleResearchPackageRecord,pid)
 if r is None: raise ValueError('research package not found.')
 return r
def create_package(db,project_id,p):
 _reject(p);_project(db,project_id)
 if not str(p.get('title') or '').strip(): raise ValueError('title is required.')
 r=ReproducibleResearchPackageRecord(project_entity_id=project_id,package_key=p['package_key'],title=p['title'],purpose=p.get('purpose'),status=p.get('status','draft'),manifest_version=p.get('manifest_version','1.0'),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_component(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);t=p['component_type']
 if t not in COMPONENT_TYPES: raise ValueError('unsupported component_type: '+t)
 r=ReproducibleResearchPackageComponentRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,component_key=p['component_key'],component_type=t,component_ref=p['component_ref'],version_ref=p.get('version_ref'),content_hash=p.get('content_hash'),required=p.get('required',True),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_artifact(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);r=ReproducibleResearchPackageArtifactRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,artifact_key=p['artifact_key'],artifact_type=p['artifact_type'],artifact_ref=p['artifact_ref'],media_type=p.get('media_type'),content_hash=p.get('content_hash'),size_bytes=p.get('size_bytes'),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_environment(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);r=ReproducibleResearchPackageEnvironmentRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,environment_key=p['environment_key'],environment_ref=p.get('environment_ref'),runtime_manifest_json=p.get('runtime_manifest',{}),dependency_manifest_json=p.get('dependency_manifest',{}),container_ref=p.get('container_ref'),hardware_json=p.get('hardware',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_replay_plan(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);prod=p.get('target_product')
 if prod and prod not in PRODUCTS: raise ValueError('unsupported Catalyst product: '+prod)
 r=ReproducibleResearchReplayPlanRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,plan_key=p['plan_key'],target_product=prod,instructions_json=p.get('instructions',{}),entrypoint_ref=p.get('entrypoint_ref'),expected_outputs_json=p.get('expected_outputs',[]),provenance_json=p.get('provenance',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_verification(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);r=ReproducibleResearchVerificationRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,verification_type=p.get('verification_type','external'),verifier_ref=p.get('verifier_ref'),status=p.get('status','recorded'),evidence_json=p.get('evidence',{}),observed_hash=p.get('observed_hash'));db.add(r);db.commit();db.refresh(r);return _ser(r)
def add_review(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);r=ReproducibleResearchReviewRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,reviewer_ref=p.get('reviewer_ref'),review_type=p.get('review_type','reproducibility'),status=p.get('status','recorded'),findings_json=p.get('findings',{}),notes=p.get('notes'));db.add(r);db.commit();db.refresh(r);return _ser(r)
def bundle(db,package_id,public=False):
 pkg=_package(db,package_id)
 def rows(cls): return [_ser(x) for x in db.scalars(select(cls).where(cls.package_id==package_id)).all()]
 return {'release':'2.75.0','contract':CONTRACT,'package':_ser(pkg),'components':rows(ReproducibleResearchPackageComponentRecord),'artifacts':rows(ReproducibleResearchPackageArtifactRecord),'environments':rows(ReproducibleResearchPackageEnvironmentRecord),'replay_plans':rows(ReproducibleResearchReplayPlanRecord),'verifications':rows(ReproducibleResearchVerificationRecord),'reviews':rows(ReproducibleResearchReviewRecord),'snapshots':rows(ReproducibleResearchSnapshotRecord),**boundaries()}
def snapshot(db,package_id,p):
 _reject(p);pkg=_package(db,package_id);state=bundle(db,package_id);state.pop('snapshots',None);h=_hash(state);prev=db.scalar(select(ReproducibleResearchSnapshotRecord).where(ReproducibleResearchSnapshotRecord.package_id==package_id).order_by(ReproducibleResearchSnapshotRecord.revision.desc()).limit(1));rev=1 if prev is None else prev.revision+1
 r=ReproducibleResearchSnapshotRecord(package_id=package_id,project_entity_id=pkg.project_entity_id,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)
