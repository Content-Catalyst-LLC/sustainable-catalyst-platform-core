from __future__ import annotations
import hashlib,json
from datetime import datetime
from sqlalchemy import func,select,inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    VisualViewCompositionRecord, VisualViewAssignmentRecord, VisualGrammarSpecificationRecord, VisualModelConstructionRecord,
    PredictiveIntelligencePackageRecord, PredictiveForecastRunRecord, PredictiveProbabilisticForecastRecord, PredictiveEnsembleForecastRecord,
    PredictiveCalibrationStudyRecord, PredictiveCalibrationMappingRecord, PredictiveEnsembleRecord, PredictiveComparisonStudyRecord,
    PredictiveMonitoringStudyRecord, PredictiveAnomalyObservationRecord, PredictiveChangePointRecord, PredictiveEarlyWarningSignalRecord,
    PredictiveSpatialTemporalStudyRecord, PredictiveSpatialTemporalForecastRecord, PredictiveSpatialUnitRecord,
    PredictiveCausalStudyRecord, PredictiveCounterfactualForecastRecord, PredictiveCausalEffectEvidenceRecord,
    PredictiveDecisionStudyRecord, PredictiveDecisionEvidenceBindingRecord, PredictiveDecisionScenarioAssessmentRecord, PredictiveDecisionEvaluationRecord,
    VisualPredictiveWorkspaceRecord, VisualForecastOverlayRecord, VisualUncertaintyDisplayRecord, VisualCalibrationDisplayRecord,
    VisualEnsembleComparisonOverlayRecord, VisualMonitoringOverlayRecord, VisualSpatialTemporalForecastLayerRecord,
    VisualCausalPredictiveOverlayRecord, VisualDecisionPredictionBindingRecord, VisualPredictiveSnapshotRecord,
)
CONTRACT="sc.visual-runtime.predictive-intelligence.v1"
FORBIDDEN={"forecast_execution_by_core","probabilistic_inference_by_core","calibration_computation_by_core","ensemble_combination_by_core","anomaly_detection_by_core","change_point_detection_by_core","spatial_prediction_by_core","counterfactual_execution_by_core","decision_optimization_by_core","visual_rendering_by_core","automatic_visual_inference"}

def _ser(row):
    out={}
    for a in sa_inspect(row).mapper.column_attrs:
        v=getattr(row,a.key)
        if isinstance(v,datetime):v=v.isoformat()
        out[a.key]=v
    for k in list(out):
        if k.endswith('_json'):out[k[:-5]]=out.pop(k)
    return out

def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def _reject(p):
    bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
    if bad:raise ValueError('Visual Predictive Intelligence is declarative; Core does not execute: '+', '.join(bad))
def boundaries():return {
 'visual_predictive_workspace_registry_by_core':True,'visual_forecast_overlay_registry_by_core':True,'visual_uncertainty_display_registry_by_core':True,
 'visual_calibration_display_registry_by_core':True,'visual_ensemble_comparison_registry_by_core':True,'visual_monitoring_overlay_registry_by_core':True,
 'visual_spatial_temporal_forecast_registry_by_core':True,'visual_causal_predictive_overlay_registry_by_core':True,'visual_decision_prediction_binding_registry_by_core':True,
 'immutable_visual_predictive_snapshots_by_core':True,'forecast_execution_by_core':False,'probabilistic_inference_by_core':False,'calibration_computation_by_core':False,
 'ensemble_combination_by_core':False,'anomaly_detection_by_core':False,'change_point_detection_by_core':False,'spatial_prediction_by_core':False,
 'counterfactual_execution_by_core':False,'decision_optimization_by_core':False,'visual_rendering_by_core':False,'automatic_visual_inference':False,
 'automatic_visual_truth_promotion':False}
def readiness(db):
    c=lambda cls:db.scalar(select(func.count()).select_from(cls)) or 0
    return {'release':'2.67.0','contract':CONTRACT,'counts':{'workspaces':c(VisualPredictiveWorkspaceRecord),'forecast_overlays':c(VisualForecastOverlayRecord),'uncertainty_displays':c(VisualUncertaintyDisplayRecord),'calibration_displays':c(VisualCalibrationDisplayRecord),'ensemble_comparisons':c(VisualEnsembleComparisonOverlayRecord),'monitoring_overlays':c(VisualMonitoringOverlayRecord),'spatial_temporal_layers':c(VisualSpatialTemporalForecastLayerRecord),'causal_overlays':c(VisualCausalPredictiveOverlayRecord),'decision_bindings':c(VisualDecisionPredictionBindingRecord),'snapshots':c(VisualPredictiveSnapshotRecord)},**boundaries()}
def _get(db,cls,id,label):
    if not id:return None
    x=db.get(cls,id)
    if not x:raise ValueError(f'{label} not found.')
    return x
def _workspace(db,wid):return _get(db,VisualPredictiveWorkspaceRecord,wid,'visual predictive workspace')
def _composition(db,cid):return _get(db,VisualViewCompositionRecord,cid,'view composition')
def _views(db,composition_id,ids):
    allowed={r.view_id for r in db.scalars(select(VisualViewAssignmentRecord).where(VisualViewAssignmentRecord.composition_id==composition_id)).all()}
    bad=[x for x in ids if x not in allowed]
    if bad:raise ValueError('target views must belong to the workspace composition: '+', '.join(bad))
def _workspace_views(db,wid,p):
    w=_workspace(db,wid);ids=p.get('target_view_ids',[]);_views(db,w.composition_id,ids);return w

def create_workspace(db:Session,composition_id:str,p:dict):
    _reject(p);comp=_composition(db,composition_id)
    gid=p.get('grammar_specification_id')
    if gid:
        g=_get(db,VisualGrammarSpecificationRecord,gid,'grammar specification')
        if g.scene_id!=comp.scene_id:raise ValueError('grammar specification must belong to the composition scene.')
    mid=p.get('model_construction_id')
    if mid:_get(db,VisualModelConstructionRecord,mid,'visual model construction')
    pkg=p.get('predictive_package_id')
    if pkg:_get(db,PredictiveIntelligencePackageRecord,pkg,'predictive intelligence package')
    row=VisualPredictiveWorkspaceRecord(composition_id=composition_id,grammar_specification_id=gid,model_construction_id=mid,predictive_package_id=pkg,workspace_key=p['workspace_key'],name=p['name'],purpose=p.get('purpose'),status=p.get('status','draft'),visibility=p.get('visibility','private'),settings_json=p.get('settings',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_forecast_overlay(db,wid,p):
    _reject(p);_workspace_views(db,wid,p)
    refs=[p.get('forecast_run_id'),p.get('probabilistic_forecast_id'),p.get('ensemble_forecast_id')]
    if not any(refs):raise ValueError('forecast overlay requires at least one predictive forecast reference.')
    _get(db,PredictiveForecastRunRecord,refs[0],'forecast run');_get(db,PredictiveProbabilisticForecastRecord,refs[1],'probabilistic forecast');_get(db,PredictiveEnsembleForecastRecord,refs[2],'ensemble forecast')
    row=VisualForecastOverlayRecord(workspace_id=wid,overlay_key=p['overlay_key'],forecast_run_id=refs[0],probabilistic_forecast_id=refs[1],ensemble_forecast_id=refs[2],target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}),metadata_json=p.get('metadata',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_uncertainty_display(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);pf=p.get('probabilistic_forecast_id');cs=p.get('calibration_study_id')
    if not pf and not cs:raise ValueError('uncertainty display requires probabilistic forecast or calibration study evidence.')
    _get(db,PredictiveProbabilisticForecastRecord,pf,'probabilistic forecast');_get(db,PredictiveCalibrationStudyRecord,cs,'calibration study')
    row=VisualUncertaintyDisplayRecord(workspace_id=wid,display_key=p['display_key'],probabilistic_forecast_id=pf,calibration_study_id=cs,display_kind=p.get('display_kind','interval-band'),interval_levels_json=p.get('interval_levels',[]),quantiles_json=p.get('quantiles',[]),target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_calibration_display(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);sid=p['calibration_study_id'];study=_get(db,PredictiveCalibrationStudyRecord,sid,'calibration study');mid=p.get('calibration_mapping_id')
    if mid:
        m=_get(db,PredictiveCalibrationMappingRecord,mid,'calibration mapping')
        if m.calibration_study_id!=study.id:raise ValueError('calibration mapping must belong to the calibration study.')
    row=VisualCalibrationDisplayRecord(workspace_id=wid,display_key=p['display_key'],calibration_study_id=sid,calibration_mapping_id=mid,display_kind=p.get('display_kind','reliability'),target_view_ids_json=p.get('target_view_ids',[]),evidence_json=p.get('evidence',{}),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_ensemble_comparison(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);eid=p.get('ensemble_id');cid=p.get('comparison_study_id');fids=p.get('ensemble_forecast_ids',[])
    if not eid and not cid and not fids:raise ValueError('ensemble comparison requires ensemble, comparison study, or forecast evidence.')
    _get(db,PredictiveEnsembleRecord,eid,'predictive ensemble');_get(db,PredictiveComparisonStudyRecord,cid,'comparison study')
    for x in fids:_get(db,PredictiveEnsembleForecastRecord,x,'ensemble forecast')
    row=VisualEnsembleComparisonOverlayRecord(workspace_id=wid,overlay_key=p['overlay_key'],ensemble_id=eid,comparison_study_id=cid,ensemble_forecast_ids_json=fids,target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_monitoring_overlay(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);sid=p.get('monitoring_study_id');a=p.get('anomaly_observation_ids',[]);c=p.get('change_point_ids',[]);e=p.get('early_warning_signal_ids',[])
    if not sid and not a and not c and not e:raise ValueError('monitoring overlay requires monitoring evidence.')
    _get(db,PredictiveMonitoringStudyRecord,sid,'monitoring study')
    for x in a:_get(db,PredictiveAnomalyObservationRecord,x,'anomaly observation')
    for x in c:_get(db,PredictiveChangePointRecord,x,'change point')
    for x in e:_get(db,PredictiveEarlyWarningSignalRecord,x,'early warning signal')
    row=VisualMonitoringOverlayRecord(workspace_id=wid,overlay_key=p['overlay_key'],monitoring_study_id=sid,anomaly_observation_ids_json=a,change_point_ids_json=c,early_warning_signal_ids_json=e,target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_spatial_temporal_layer(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);sid=p['spatial_temporal_study_id'];_get(db,PredictiveSpatialTemporalStudyRecord,sid,'spatial-temporal study');fids=p.get('forecast_ids',[]);uids=p.get('spatial_unit_ids',[])
    for x in fids:
        f=_get(db,PredictiveSpatialTemporalForecastRecord,x,'spatial-temporal forecast')
        if f.spatial_temporal_study_id!=sid:raise ValueError('spatial-temporal forecast must belong to the study.')
    for x in uids:
        u=_get(db,PredictiveSpatialUnitRecord,x,'spatial unit')
        if u.spatial_temporal_study_id!=sid:raise ValueError('spatial unit must belong to the study.')
    row=VisualSpatialTemporalForecastLayerRecord(workspace_id=wid,layer_key=p['layer_key'],spatial_temporal_study_id=sid,forecast_ids_json=fids,spatial_unit_ids_json=uids,target_view_ids_json=p.get('target_view_ids',[]),temporal_window_json=p.get('temporal_window',{}),layer_contract_json=p.get('layer_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_causal_overlay(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);sid=p['causal_predictive_study_id'];_get(db,PredictiveCausalStudyRecord,sid,'causal-predictive study');cf=p.get('counterfactual_forecast_ids',[]);ef=p.get('causal_effect_evidence_ids',[])
    for x in cf:
        r=_get(db,PredictiveCounterfactualForecastRecord,x,'counterfactual forecast')
        if r.causal_predictive_study_id!=sid:raise ValueError('counterfactual forecast must belong to the study.')
    for x in ef:
        r=_get(db,PredictiveCausalEffectEvidenceRecord,x,'causal effect evidence')
        if r.causal_predictive_study_id!=sid:raise ValueError('causal effect evidence must belong to the study.')
    row=VisualCausalPredictiveOverlayRecord(workspace_id=wid,overlay_key=p['overlay_key'],causal_predictive_study_id=sid,counterfactual_forecast_ids_json=cf,causal_effect_evidence_ids_json=ef,target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def create_decision_binding(db,wid,p):
    _reject(p);_workspace_views(db,wid,p);sid=p['decision_study_id'];_get(db,PredictiveDecisionStudyRecord,sid,'predictive decision study');eb=p.get('evidence_binding_ids',[]);sa=p.get('scenario_assessment_ids',[]);ev=p.get('evaluation_ids',[])
    for cls,ids,label in ((PredictiveDecisionEvidenceBindingRecord,eb,'decision evidence binding'),(PredictiveDecisionScenarioAssessmentRecord,sa,'scenario assessment'),(PredictiveDecisionEvaluationRecord,ev,'decision evaluation')):
        for x in ids:
            r=_get(db,cls,x,label)
            if r.decision_study_id!=sid:raise ValueError(f'{label} must belong to the decision study.')
    row=VisualDecisionPredictionBindingRecord(workspace_id=wid,binding_key=p['binding_key'],decision_study_id=sid,evidence_binding_ids_json=eb,scenario_assessment_ids_json=sa,evaluation_ids_json=ev,target_view_ids_json=p.get('target_view_ids',[]),display_contract_json=p.get('display_contract',{}),provenance_json=p.get('provenance',{}));db.add(row);db.commit();db.refresh(row);return _ser(row)
def workspace_bundle(db,wid,public_only=False):
    w=_workspace(db,wid)
    if public_only and w.visibility!='public':raise ValueError('visual predictive workspace is not public.')
    def rows(cls):return [_ser(r) for r in db.scalars(select(cls).where(cls.workspace_id==wid)).all()]
    return {'contract':CONTRACT,'workspace':_ser(w),'forecast_overlays':rows(VisualForecastOverlayRecord),'uncertainty_displays':rows(VisualUncertaintyDisplayRecord),'calibration_displays':rows(VisualCalibrationDisplayRecord),'ensemble_comparisons':rows(VisualEnsembleComparisonOverlayRecord),'monitoring_overlays':rows(VisualMonitoringOverlayRecord),'spatial_temporal_layers':rows(VisualSpatialTemporalForecastLayerRecord),'causal_overlays':rows(VisualCausalPredictiveOverlayRecord),'decision_bindings':rows(VisualDecisionPredictionBindingRecord),'snapshots':rows(VisualPredictiveSnapshotRecord),'boundaries':boundaries()}
def create_snapshot(db,wid,p):
    _reject(p);state=workspace_bundle(db,wid);state.pop('snapshots',None);prevs=db.scalars(select(VisualPredictiveSnapshotRecord).where(VisualPredictiveSnapshotRecord.workspace_id==wid).order_by(VisualPredictiveSnapshotRecord.revision.asc())).all();rev=len(prevs)+1;prev=prevs[-1].content_hash if prevs else None;h=_hash({'revision':rev,'previous_snapshot_hash':prev,'state':state});row=VisualPredictiveSnapshotRecord(workspace_id=wid,revision=rev,content_hash=h,previous_snapshot_hash=prev,state_json=state,provenance_json=p.get('provenance',{}),created_by=p.get('created_by','operator'));db.add(row);db.commit();db.refresh(row);return _ser(row)
