#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_objects,model_canvas,visualization_registry

def main():
    settings=Settings.from_env();db=Database(settings.database_url);run_migrations(db);status=migration_status(db);assert '0037' in status['applied'] and not status['pending'],status
    with db.session_factory() as s:
        p=research_objects.create_object(s,object_type='research-project',name='Canvas validator project',slug='v234-validator-project',description='validator',visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'research_question':'Inspect model controls'},release='2.34.0')
        m=research_objects.create_object(s,object_type='model',name='Validator model',slug='v234-validator-model',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]},release='2.34.0')
        param=research_objects.create_object(s,object_type='parameter',name='Efficiency',slug='v234-validator-efficiency',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'model_entity_id':m['id'],'name':'efficiency','data_type':'number','unit':'percent','default_value':{'value':80},'bounds':{'min':0,'max':100}},release='2.34.0')
        c=model_canvas.create_canvas(s,{'name':'Validator canvas','slug':'v234-validator-canvas','project_entity_id':p['id'],'model_entity_id':m['id'],'visibility':'public'},release='2.34.0');cid=c['visual_entity_id']
        n=model_canvas.add_node(s,cid,{'node_key':'efficiency','node_kind':'parameter','semantic_role':'parameter','bound_entity_id':param['id'],'label':'Efficiency','unit':'percent'})
        ctrl=model_canvas.add_control(s,cid,{'control_key':'efficiency-slider','control_kind':'slider','node_id':n['id'],'bound_entity_id':param['id'],'label':'Efficiency','data_type':'number','unit':'percent','bounds':{'min':0,'max':100},'handoff':{'product':'lab','action':'request-run'}})
        state=model_canvas.save_state(s,cid,{'state_key':'default','name':'Default','values':{'efficiency':80},'provenance':{'source':'validator'}});assert len(state['state_hash'])==64 and state['immutable'] is True
        val=model_canvas.validate_structure(s,cid);assert val['valid'] and not val['model_execution_performed'] and not val['numerical_computation_performed']
        spec=model_canvas.compile_specification(s,cid,{'spec_key':'validator','spec_kind':'diagram','created_by':'validator'});assert spec['metadata_json']['interactive_model_canvas_v234'] is True
        resolved=visualization_registry.resolve_renderer(s,spec['id'],created_by='validator');assert resolved['resolved_renderer_key']=='contract.d3' and resolved['execution_performed'] is False
        ready=model_canvas.readiness(s);assert ready['model_execution_by_core'] is False and ready['external_execution_handoff'] is True
    print({'version':'2.34.0','migration_0037_applied':True,'interactive_model_canvas':True,'research_models_reused':True,'external_execution_handoff':True,'model_execution_by_core':False,'numerical_computation_by_core':False,'layout_execution_by_core':False})
    print('PASS - Core 2.34.0 Interactive Model Canvas validation')
if __name__=='__main__':main()
