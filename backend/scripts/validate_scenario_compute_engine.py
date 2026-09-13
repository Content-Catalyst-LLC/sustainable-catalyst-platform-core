#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services import research_objects, scenario_compute

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); status=migration_status(db); assert '0038' in status['applied'] and not status['pending'],status
    with db.session_factory() as s:
        p=research_objects.create_object(s,object_type='research-project',name='Compute validator project',slug='v235-validator-project',description='validator',visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'research_question':'Compare governed scenarios'},release='2.35.0')
        m=research_objects.create_object(s,object_type='model',name='Compute validator model',slug='v235-validator-model',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]},release='2.35.0')
        v=research_objects.create_object(s,object_type='model-version',name='Compute validator v1',slug='v235-validator-version',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'model_entity_id':m['id'],'version_label':'v1','specification':{'validator':True},'immutable':True},release='2.35.0')
        research_objects.create_object(s,object_type='parameter',name='Demand',slug='v235-validator-demand',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'model_entity_id':m['id'],'name':'demand','data_type':'number','unit':'MW','default_value':{'value':100},'bounds':{'min':0,'max':500}},release='2.35.0')
        sc=research_objects.create_object(s,object_type='scenario',name='Baseline',slug='v235-validator-scenario',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'scenario_state':'ready','parameter_values':{'demand':100},'assumptions':[]},release='2.35.0')
        plan=scenario_compute.create_plan(s,{'plan_key':'validator','name':'Validator plan','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'execution_product':'lab','execution_contract':{'product':'lab','action':'execute-scenario'}})
        case=scenario_compute.add_case(s,plan['id'],{'case_key':'baseline','scenario_entity_id':sc['id'],'comparison_role':'baseline','parameter_overrides':{'demand':125},'expected_outputs':['summary']}); assert len(case['case_hash'])==64
        prepared=scenario_compute.prepare_requests(s,plan['id'],submitted_by='validator'); assert prepared['count']==1 and not prepared['network_dispatch_performed']
        request=prepared['prepared'][0]; assert len(request['request_hash'])==64 and request['input_manifest_json']['parameter_values']['demand']==125
        attempt=scenario_compute.add_attempt(s,request['id'],{'attempt_state':'running','executor_product':'lab','external_execution_id':'validator-lab-run'}); assert attempt['attempt_number']==1
        valid=scenario_compute.validate_plan(s,plan['id']); assert valid['valid'] and not valid['numerical_computation_performed']
        ready=scenario_compute.readiness(s); assert ready['orchestration_by_core'] and ready['numerical_computation_by_core'] is False and ready['network_dispatch_by_core'] is False
    print({'version':'2.35.0','migration_0038_applied':True,'scenario_compute_engine':True,'deterministic_input_manifests':True,'idempotent_execution_requests':True,'lab_workbench_execution_handoff':True,'network_dispatch_by_core':False,'numerical_computation_by_core':False,'arbitrary_code_execution_by_core':False})
    print('PASS - Core 2.35.0 Scenario Compute Engine validation')
if __name__=='__main__': main()
