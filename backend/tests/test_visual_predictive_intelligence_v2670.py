from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import (
 Entity,VisualRuntimeSceneRecord,VisualRuntimeViewRecord,VisualViewCompositionRecord,VisualViewAssignmentRecord,VisualGrammarSpecificationRecord,
 PredictiveModelRecord,PredictiveTargetRecord,PredictiveForecastRunRecord,PredictiveProbabilisticForecastRecord,PredictiveCalibrationStudyRecord,PredictiveCalibrationMappingRecord,
 PredictiveEnsembleRecord,PredictiveComparisonStudyRecord,PredictiveMonitoringStudyRecord,PredictiveAnomalyObservationRecord,PredictiveChangePointRecord,PredictiveEarlyWarningSignalRecord,
 PredictiveSpatialTemporalStudyRecord,PredictiveSpatialUnitRecord,PredictiveSpatialTemporalForecastRecord,CausalGraphRecord,PredictiveCausalStudyRecord,PredictiveCounterfactualForecastRecord,PredictiveCausalEffectEvidenceRecord,
 PredictiveDecisionStudyRecord,PredictiveDecisionOptionRecord,PredictiveDecisionEvidenceBindingRecord,PredictiveDecisionScenarioAssessmentRecord,PredictiveDecisionEvaluationRecord,
)

def seed(app):
 with app.state.database.session_factory() as db:
  p=Entity(id='project:v267',entity_type='research-project',slug='v267',name='Visual Predictive Project',visibility='public');db.add(p);db.flush()
  scene=VisualRuntimeSceneRecord(project_entity_id=p.id,scene_key='predictive',name='Predictive Scene',visibility='public');db.add(scene);db.flush()
  view=VisualRuntimeViewRecord(scene_id=scene.id,view_key='forecast',name='Forecast',view_kind='chart');db.add(view);db.flush()
  comp=VisualViewCompositionRecord(scene_id=scene.id,composition_key='predictive',name='Predictive Composition',visibility='public');db.add(comp);db.flush();db.add(VisualViewAssignmentRecord(composition_id=comp.id,view_id=view.id));
  gram=VisualGrammarSpecificationRecord(scene_id=scene.id,grammar_key='forecast-grammar',name='Forecast Grammar',grammar_kind='layered',visibility='public');db.add(gram);db.flush()
  model=PredictiveModelRecord(project_entity_id=p.id,model_key='load',name='Load Forecast',visibility='public');db.add(model);db.flush()
  target=PredictiveTargetRecord(model_id=model.id,target_key='demand',label='Demand');db.add(target);db.flush()
  run=PredictiveForecastRunRecord(model_id=model.id,run_key='run-1');db.add(run);db.flush()
  prob=PredictiveProbabilisticForecastRecord(model_id=model.id,target_id=target.id,forecast_run_id=run.id,representation='quantile',forecast_json={'quantiles':{'0.1':1,'0.5':2,'0.9':3}});db.add(prob);db.flush()
  cal=PredictiveCalibrationStudyRecord(model_id=model.id,target_id=target.id,study_key='cal');db.add(cal);db.flush()
  cmap=PredictiveCalibrationMappingRecord(calibration_study_id=cal.id,mapping_key='map',method='isotonic');db.add(cmap);db.flush()
  ens=PredictiveEnsembleRecord(project_entity_id=p.id,ensemble_key='ens',name='Ensemble',visibility='public');cmp=PredictiveComparisonStudyRecord(project_entity_id=p.id,comparison_key='cmp',name='Comparison',visibility='public');db.add_all([ens,cmp]);db.flush()
  mon=PredictiveMonitoringStudyRecord(project_entity_id=p.id,model_id=model.id,target_id=target.id,study_key='mon',name='Monitoring',visibility='public');db.add(mon);db.flush()
  ano=PredictiveAnomalyObservationRecord(monitoring_study_id=mon.id,observation_key='a1',score_json={'score':3});chg=PredictiveChangePointRecord(monitoring_study_id=mon.id,change_key='c1',method='external',statistic_json={'score':2});warn=PredictiveEarlyWarningSignalRecord(monitoring_study_id=mon.id,signal_key='w1',signal_kind='threshold',indicator_json={'value':1});db.add_all([ano,chg,warn]);db.flush()
  st=PredictiveSpatialTemporalStudyRecord(project_entity_id=p.id,study_key='sp',name='Spatial',visibility='public');db.add(st);db.flush();unit=PredictiveSpatialUnitRecord(spatial_temporal_study_id=st.id,unit_key='u1',label='Unit');db.add(unit);db.flush();spf=PredictiveSpatialTemporalForecastRecord(spatial_temporal_study_id=st.id,spatial_unit_id=unit.id,forecast_key='sf1',forecast_json={'value':4});db.add(spf);db.flush()
  cg=CausalGraphRecord(graph_key='cg',name='Causal Graph',project_entity_id=p.id);db.add(cg);db.flush();cs=PredictiveCausalStudyRecord(project_entity_id=p.id,predictive_model_id=model.id,causal_graph_id=cg.entity_id if hasattr(cg,'entity_id') else cg.id,study_key='causal',name='Causal Predictive',visibility='public');db.add(cs);db.flush();cf=PredictiveCounterfactualForecastRecord(causal_predictive_study_id=cs.id,forecast_key='cf1',counterfactual_forecast_json={'value':5});ce=PredictiveCausalEffectEvidenceRecord(causal_predictive_study_id=cs.id,evidence_key='e1',effect_json={'ate':1.2});db.add_all([cf,ce]);db.flush()
  ds=PredictiveDecisionStudyRecord(project_entity_id=p.id,predictive_model_id=model.id,study_key='dec',name='Decision',visibility='public');db.add(ds);db.flush();opt=PredictiveDecisionOptionRecord(decision_study_id=ds.id,option_key='o1',name='Option',action_json={'action':'hold'});db.add(opt);db.flush();de=PredictiveDecisionEvidenceBindingRecord(decision_study_id=ds.id,binding_key='b1',option_id=opt.id,evidence_kind='forecast',forecast_run_id=run.id);sa=PredictiveDecisionScenarioAssessmentRecord(decision_study_id=ds.id,option_id=opt.id,assessment_key='s1',scenario_json={'scenario':'base'},outcome_evidence_json={'value':2});ev=PredictiveDecisionEvaluationRecord(decision_study_id=ds.id,evaluation_key='ev1',option_id=opt.id,metric_evidence_json={'metric':1});db.add_all([de,sa,ev]);db.commit()
  return {'composition':comp.id,'view':view.id,'grammar':gram.id,'run':run.id,'prob':prob.id,'cal':cal.id,'cmap':cmap.id,'ens':ens.id,'cmp':cmp.id,'mon':mon.id,'ano':ano.id,'chg':chg.id,'warn':warn.id,'sp':st.id,'unit':unit.id,'spf':spf.id,'causal':cs.id,'cf':cf.id,'ce':ce.id,'decision':ds.id,'de':de.id,'sa':sa.id,'ev':ev.id}

def test_readiness_and_full_visual_predictive_roundtrip(tmp_path):
 app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v267.db'}",version='2.67.0'));c=TestClient(app);x=seed(app)
 d=c.get('/v1/visual-runtime/predictive/readiness').json();assert d['release']=='2.67.0' and d['migration_0071_applied'] and d['forecast_execution_by_core'] is False
 ws=c.post(f"/v1/visual-runtime/predictive/compositions/{x['composition']}/workspaces",json={'data':{'workspace_key':'risk','name':'Risk Forecast Workspace','grammar_specification_id':x['grammar'],'visibility':'public'}});assert ws.status_code==200,ws.text;wid=ws.json()['id'];v=[x['view']]
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/forecast-overlays',json={'data':{'overlay_key':'forecast','forecast_run_id':x['run'],'probabilistic_forecast_id':x['prob'],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/uncertainty-displays',json={'data':{'display_key':'unc','probabilistic_forecast_id':x['prob'],'calibration_study_id':x['cal'],'interval_levels':[0.5,0.9],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/calibration-displays',json={'data':{'display_key':'cal','calibration_study_id':x['cal'],'calibration_mapping_id':x['cmap'],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/ensemble-comparisons',json={'data':{'overlay_key':'ens','ensemble_id':x['ens'],'comparison_study_id':x['cmp'],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/monitoring-overlays',json={'data':{'overlay_key':'mon','monitoring_study_id':x['mon'],'anomaly_observation_ids':[x['ano']],'change_point_ids':[x['chg']],'early_warning_signal_ids':[x['warn']],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/spatial-temporal-layers',json={'data':{'layer_key':'sp','spatial_temporal_study_id':x['sp'],'forecast_ids':[x['spf']],'spatial_unit_ids':[x['unit']],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/causal-overlays',json={'data':{'overlay_key':'causal','causal_predictive_study_id':x['causal'],'counterfactual_forecast_ids':[x['cf']],'causal_effect_evidence_ids':[x['ce']],'target_view_ids':v}}).status_code==200
 assert c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/decision-bindings',json={'data':{'binding_key':'dec','decision_study_id':x['decision'],'evidence_binding_ids':[x['de']],'scenario_assessment_ids':[x['sa']],'evaluation_ids':[x['ev']],'target_view_ids':v}}).status_code==200
 s1=c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/snapshots',json={'data':{'created_by':'test'}}).json();s2=c.post(f'/v1/visual-runtime/predictive/workspaces/{wid}/snapshots',json={'data':{'created_by':'test'}}).json();assert s2['previous_snapshot_hash']==s1['content_hash']
 b=c.get(f'/v1/visual-runtime/predictive/workspaces/{wid}/bundle').json();assert b['contract']=='sc.visual-runtime.predictive-intelligence.v1' and len(b['forecast_overlays'])==1 and len(b['decision_bindings'])==1 and b['boundaries']['decision_optimization_by_core'] is False

def test_execution_and_cross_view_boundaries(tmp_path):
 app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v267b.db'}",version='2.67.0'));c=TestClient(app);x=seed(app)
 bad=c.post(f"/v1/visual-runtime/predictive/compositions/{x['composition']}/workspaces",json={'data':{'workspace_key':'bad','name':'Bad','forecast_execution_by_core':True}});assert bad.status_code==422
 ws=c.post(f"/v1/visual-runtime/predictive/compositions/{x['composition']}/workspaces",json={'data':{'workspace_key':'ok','name':'OK'}}).json()['id']
 bad2=c.post(f'/v1/visual-runtime/predictive/workspaces/{ws}/forecast-overlays',json={'data':{'overlay_key':'bad-view','forecast_run_id':x['run'],'target_view_ids':['not-assigned']}});assert bad2.status_code==422
