from __future__ import annotations
import hashlib,json
from datetime import datetime
from sqlalchemy import func,select,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import *
CONTRACT="sc.visual-runtime.forensics-workbench.v1"
FORBIDDEN={"evidence_authentication_by_core","guilt_inference_by_core","automatic_reconstruction_by_core","media_forensics_execution_by_core","quantitative_reconstruction_execution_by_core","graph_inference_by_core","visual_rendering_by_core","automatic_visual_inference"}
def _ser(row):
 out={}
 for a in sa_inspect(row).mapper.column_attrs:
  v=getattr(row,a.key);out[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(out):
  if k.endswith('_json'):out[k[:-5]]=out.pop(k)
 return out
def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad:raise ValueError('Visual Forensics Workbench is declarative; Core does not execute: '+', '.join(bad))
def boundaries():return {'visual_forensic_workspace_registry_by_core':True,'visual_forensic_evidence_binding_registry_by_core':True,'visual_forensic_claim_overlay_registry_by_core':True,'visual_forensic_timeline_registry_by_core':True,'visual_forensic_spatial_temporal_registry_by_core':True,'visual_forensic_media_registry_by_core':True,'visual_forensic_reconstruction_registry_by_core':True,'visual_forensic_documentary_registry_by_core':True,'visual_forensic_graph_registry_by_core':True,'immutable_visual_forensic_snapshots_by_core':True,'evidence_authentication_by_core':False,'guilt_inference_by_core':False,'automatic_reconstruction_by_core':False,'media_forensics_execution_by_core':False,'quantitative_reconstruction_execution_by_core':False,'graph_inference_by_core':False,'visual_rendering_by_core':False,'automatic_visual_inference':False,'automatic_visual_truth_promotion':False}
CLASSES=[VisualForensicWorkspaceRecord,VisualForensicEvidenceBindingRecord,VisualForensicClaimOverlayRecord,VisualForensicTimelineLayerRecord,VisualForensicSpatialTemporalLayerRecord,VisualForensicMediaLayerRecord,VisualForensicReconstructionBindingRecord,VisualForensicDocumentaryBindingRecord,VisualForensicGraphBindingRecord,VisualForensicSnapshotRecord]
def readiness(db):
 c=lambda x:db.scalar(select(func.count()).select_from(x)) or 0
 names=['workspaces','evidence_bindings','claim_overlays','timeline_layers','spatial_temporal_layers','media_layers','reconstruction_bindings','documentary_bindings','graph_bindings','snapshots']
 return {'release':'2.68.0','contract':CONTRACT,'counts':dict(zip(names,[c(x) for x in CLASSES])),**boundaries()}
def _get(db,cls,id,label):
 x=db.get(cls,id) if id else None
 if not x:raise ValueError(label+' not found.')
 return x
def _workspace(db,wid):return _get(db,VisualForensicWorkspaceRecord,wid,'visual forensic workspace')
def _views(db,cid,ids):
 allowed={r.view_id for r in db.scalars(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==cid)).all()}
 bad=[x for x in ids if x not in allowed]
 if bad:raise ValueError('target views must belong to the workspace composition: '+', '.join(bad))
def create_workspace(db,composition_id,p):
 _reject(p);_get(db,VisualViewCompositionRecord,composition_id,'view composition');_get(db,ForensicInvestigationRecord,p['investigation_id'],'forensic investigation')
 r=VisualForensicWorkspaceRecord(composition_id=composition_id,investigation_id=p['investigation_id'],workspace_key=p['workspace_key'],name=p['name'],purpose=p.get('purpose'),status=p.get('status','draft'),visibility=p.get('visibility','private'),settings_json=p.get('settings',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}));db.add(r);db.commit();db.refresh(r);return _ser(r)
def _child(db,wid,p,cls,key,extra):
 _reject(p);w=_workspace(db,wid);_views(db,w.composition_id,p.get('target_view_ids',[]));kw={'workspace_id':wid,key:p[key],'target_view_ids_json':p.get('target_view_ids',[]),'provenance_json':p.get('provenance',{})}
 for field,default in extra:kw[field+'_json']=p.get(field,default)
 r=cls(**kw);db.add(r);db.commit();db.refresh(r);return _ser(r)
def evidence(db,w,p):return _child(db,w,p,VisualForensicEvidenceBindingRecord,'binding_key',[('evidence_item_ids',[]),('display_contract',{})])
def claims(db,w,p):return _child(db,w,p,VisualForensicClaimOverlayRecord,'overlay_key',[('claim_ids',[]),('hypothesis_ids',[]),('contradiction_ids',[]),('display_contract',{})])
def timeline(db,w,p):return _child(db,w,p,VisualForensicTimelineLayerRecord,'layer_key',[('event_ids',[]),('reconstruction_ids',[]),('temporal_window',{})])
def spatial(db,w,p):return _child(db,w,p,VisualForensicSpatialTemporalLayerRecord,'layer_key',[('place_ids',[]),('trajectory_ids',[]),('intersection_ids',[]),('layer_contract',{})])
def media(db,w,p):return _child(db,w,p,VisualForensicMediaLayerRecord,'layer_key',[('media_artifact_ids',[]),('comparison_ids',[]),('display_contract',{})])
def reconstruction(db,w,p):return _child(db,w,p,VisualForensicReconstructionBindingRecord,'binding_key',[('reconstruction_ids',[]),('result_binding_ids',[]),('display_contract',{})])
def documentary(db,w,p):return _child(db,w,p,VisualForensicDocumentaryBindingRecord,'binding_key',[('statement_ids',[]),('document_ids',[]),('display_contract',{})])
def graph(db,w,p):return _child(db,w,p,VisualForensicGraphBindingRecord,'binding_key',[('research_graph_ids',[]),('package_ids',[]),('display_contract',{})])
def bundle(db,wid,public_only=False):
 w=_workspace(db,wid)
 if public_only and w.visibility!='public':raise ValueError('visual forensic workspace is not public.')
 out={'contract':CONTRACT,'workspace':_ser(w),'boundaries':boundaries()}
 for name,cls in zip(['evidence_bindings','claim_overlays','timeline_layers','spatial_temporal_layers','media_layers','reconstruction_bindings','documentary_bindings','graph_bindings'],CLASSES[1:9]):out[name]=[_ser(x) for x in db.scalars(select(cls).where(cls.workspace_id==wid)).all()]
 out['snapshots']=[_ser(x) for x in db.scalars(select(VisualForensicSnapshotRecord).where(VisualForensicSnapshotRecord.workspace_id==wid)).all()];return out
def snapshot(db,wid,p):
 _reject(p);state=bundle(db,wid);state.pop('snapshots',None);prev=db.scalars(select(VisualForensicSnapshotRecord).where(VisualForensicSnapshotRecord.workspace_id==wid).order_by(VisualForensicSnapshotRecord.revision.asc())).all();rev=len(prev)+1;ph=prev[-1].content_hash if prev else None;h=_hash({'revision':rev,'previous_snapshot_hash':ph,'state':state});r=VisualForensicSnapshotRecord(workspace_id=wid,revision=rev,content_hash=h,previous_snapshot_hash=ph,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(r);db.commit();db.refresh(r);return _ser(r)
