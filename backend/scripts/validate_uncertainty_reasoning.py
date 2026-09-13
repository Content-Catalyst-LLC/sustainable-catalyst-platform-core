#!/usr/bin/env python3
from tempfile import TemporaryDirectory
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_objects,uncertainty_reasoning as ur

def main():
  with TemporaryDirectory() as td:
    settings=Settings(database_url=f"sqlite:///{Path(td)/'v236.db'}",version='2.36.0',scientific_object_storage_root=str(Path(td)/'objects'))
    db=Database(settings.database_url);run_migrations(db);status=migration_status(db);assert '0039' in status['applied'] and not status['pending'],status
    with db.session_factory() as s:
      p=research_objects.create_object(s,object_type='research-project',name='UQ validator project',slug='v236-project',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'research_question':'Uncertainty'},release='2.36.0')
      m=research_objects.create_object(s,object_type='model',name='UQ validator model',slug='v236-model',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]},release='2.36.0')
      v=research_objects.create_object(s,object_type='model-version',name='UQ validator v1',slug='v236-v1',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'model_entity_id':m['id'],'version_label':'v1','specification':{},'immutable':True},release='2.36.0')
      q=research_objects.create_object(s,object_type='parameter',name='Demand',slug='v236-demand',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'model_entity_id':m['id'],'name':'demand','data_type':'number','unit':'MW','default_value':{'value':100},'bounds':{'min':0,'max':500}},release='2.36.0')
      u=ur.create_uncertainty(s,{'uncertainty_key':'demand','name':'Demand UQ','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'target_entity_id':q['id'],'uncertainty_kind':'distribution','distribution_name':'triangular','lower_bound':80,'upper_bound':120,'parameters':{'mode':100}})
      st=ur.create_sensitivity_study(s,{'study_key':'study','name':'Study','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'method':'sobol','output_key':'cost'},release='2.36.0')
      f=ur.add_factor(s,st['visual_entity_id'],{'factor_key':'demand','parameter_entity_id':q['id'],'uncertainty_definition_id':u['id'],'lower_bound':80,'upper_bound':120})
      ur.add_sensitivity_result(s,st['visual_entity_id'],{'factor_id':f['id'],'metric_kind':'sobol-first','output_key':'cost','value':{'value':0.42},'source_execution':{'executor':'lab'}})
      sv=ur.validate_sensitivity(s,st['visual_entity_id']);assert sv['valid'] and not sv['sensitivity_calculation_performed']
      ens=ur.create_ensemble(s,{'ensemble_key':'ensemble','name':'Ensemble','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id']},release='2.36.0')
      assert ur.validate_ensemble(s,ens['visual_entity_id'])['aggregation_performed'] is False
      ready=ur.readiness(s);assert ready['uncertainty_first_class'] and ready['monte_carlo_execution_by_core'] is False
    print({'version':'2.36.0','migration_0039_applied':True,'uncertainty_first_class':True,'sensitivity_reasoning':True,'ensemble_reasoning':True,'sampling_execution_by_core':False,'sensitivity_calculation_by_core':False,'ensemble_aggregation_by_core':False,'numerical_computation_by_core':False})
    print('PASS - Core 2.36.0 Uncertainty, Sensitivity & Ensemble Reasoning validation')
if __name__=='__main__':main()
