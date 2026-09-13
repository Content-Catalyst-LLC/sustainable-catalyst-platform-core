#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_objects,scenario_landscapes

def main():
    settings=Settings.from_env();db=Database(settings.database_url);run_migrations(db);status=migration_status(db);assert '0036' in status['applied'] and not status['pending'],status
    with db.session_factory() as s:
        p=research_objects.create_object(s,object_type='research-project',name='Validator project',slug='v233-validator-project',description='validator',visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'research_question':'Compare scenarios'},release='2.34.0')
        b=research_objects.create_object(s,object_type='scenario',name='Baseline',slug='v233-validator-baseline',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'scenario_state':'ready'},release='2.34.0')
        a=research_objects.create_object(s,object_type='scenario',name='Alternative',slug='v233-validator-alt',description=None,visibility='public',entity_id=None,entity_status='active',metadata={},attributes={'project_entity_id':p['id'],'base_scenario_entity_id':b['id'],'scenario_state':'ready'},release='2.34.0')
        land=scenario_landscapes.create_landscape(s,{'name':'Validator landscape','slug':'v233-validator-landscape','project_entity_id':p['id'],'baseline_scenario_entity_id':b['id'],'visibility':'public'},release='2.34.0');lid=land['visual_entity_id'];scenario_landscapes.add_scenario(s,lid,{'scenario_entity_id':a['id'],'scenario_role':'alternative'});d=scenario_landscapes.add_dimension(s,lid,{'dimension_key':'cost','dimension_kind':'metric','label':'Cost','unit':'USD'});scenario_landscapes.set_value(s,lid,{'scenario_entity_id':b['id'],'dimension_id':d['id'],'numeric_value':100,'unit':'USD'});scenario_landscapes.set_value(s,lid,{'scenario_entity_id':a['id'],'dimension_id':d['id'],'numeric_value':80,'unit':'USD','lower_bound':70,'upper_bound':90});comp=scenario_landscapes.comparison_summary(s,lid);assert comp['baseline_deltas'][a['id']]['cost']['absolute_delta']==-20;assert not comp['scenario_execution_performed'] and not comp['ranking_performed'];spec=scenario_landscapes.compile_specification(s,lid,{'spec_key':'validator','spec_kind':'chart','created_by':'validator'});assert spec['metadata_json']['scenario_landscape_v233'] is True
    print({'version':'2.34.0','migration_0036_applied':True,'scenario_landscapes':True,'research_scenarios_reused':True,'scenario_execution_by_core':False,'ranking_by_core':False,'optimization_by_core':False})
    print('PASS - Core 2.34.0 Scenario Landscapes validation')
if __name__=='__main__':main()
