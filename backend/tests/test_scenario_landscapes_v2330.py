from __future__ import annotations
from app.migrations import MIGRATIONS

def _research(client,headers,object_type,name,attrs,visibility='public'):
    r=client.post('/v1/research-objects',headers=headers,json={'object_type':object_type,'name':name,'visibility':visibility,'attributes':attrs})
    assert r.status_code==200,r.text;return r.json()
def _project(client,h):return _research(client,h,'research-project','Energy pathways',{'research_question':'Compare pathways'})
def _scenario(client,h,pid,name,base=None):return _research(client,h,'scenario',name,{'project_entity_id':pid,'base_scenario_entity_id':base,'scenario_state':'ready','parameter_values':{},'assumptions':[]})
def _landscape(client,h,pid,baseline,visibility='public'):
    r=client.post('/v1/scenario-landscapes',headers=h,json={'name':'Energy futures','visibility':visibility,'project_entity_id':pid,'baseline_scenario_entity_id':baseline,'comparison_mode':'baseline-relative','landscape_state':'draft','objective':'Compare futures','dimension_policy':'mixed','assumptions':['Values supplied by upstream analyses'],'metadata':{'v233':True}});assert r.status_code==200,r.text;return r.json()
def _public_key(client,h):
    app=client.post('/v1/developer/applications',headers=h,json={'name':'Scenario Landscape Test','owner_name':'Tester','owner_email':'scenario@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read public scenario landscapes.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'});assert app.status_code in (200,201),app.text
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=h,json={'label':'Scenario landscapes','scopes':['data:read'],'created_by':'admin'});assert issued.status_code in (200,201),issued.text;return issued.json()['api_key']

def test_v233_health_migration_and_readiness(client):
    assert any(v=='0036' for v,_ in MIGRATIONS);health=client.get('/health').json();assert health['version']=='2.37.0' and health['scenario_landscapes'] is True
    ready=client.get('/v1/scenario-landscapes/readiness').json();assert ready['release']=='2.37.0' and ready['migration_0036_applied'] is True and ready['visual_kind']=='scenario-landscape';assert ready['research_scenarios_reused'] is True;assert ready['scenario_execution_by_core'] is False and ready['ranking_by_core'] is False and ready['automatic_truth_promotion'] is False

def test_membership_dimensions_values_baseline_summary(client,write_headers):
    p=_project(client,write_headers);pid=p['id'];base=_scenario(client,write_headers,pid,'Baseline');alt=_scenario(client,write_headers,pid,'High renewables',base['id']);land=_landscape(client,write_headers,pid,base['id']);lid=land['visual_entity_id']
    a=client.post(f'/v1/scenario-landscapes/{lid}/scenarios',headers=write_headers,json={'data':{'scenario_entity_id':alt['id'],'scenario_role':'alternative'}});assert a.status_code==200,a.text
    dim=client.post(f'/v1/scenario-landscapes/{lid}/dimensions',headers=write_headers,json={'data':{'dimension_key':'emissions','dimension_kind':'metric','label':'Emissions','unit':'MtCO2e','preference_direction':'lower-better'}});assert dim.status_code==200,dim.text;did=dim.json()['id']
    for sid,val,lo,hi in [(base['id'],100,95,105),(alt['id'],60,50,70)]:
        r=client.post(f'/v1/scenario-landscapes/{lid}/values',headers=write_headers,json={'data':{'scenario_entity_id':sid,'dimension_id':did,'numeric_value':val,'unit':'MtCO2e','lower_bound':lo,'upper_bound':hi,'uncertainty':{'kind':'interval'},'provenance':{'source':'lab'}}});assert r.status_code==200,r.text
    comp=client.get(f'/v1/scenario-landscapes/{lid}/comparison').json();assert comp['baseline_deltas'][alt['id']]['emissions']['absolute_delta']==-40;assert comp['unit_conversion_performed'] is False and comp['ranking_performed'] is False and comp['scenario_execution_performed'] is False

def test_cross_project_scenario_rejected(client,write_headers):
    p1=_project(client,write_headers);p2=_research(client,write_headers,'research-project','Other',{'research_question':'Other'});base=_scenario(client,write_headers,p1['id'],'Base');other=_scenario(client,write_headers,p2['id'],'Other scenario');land=_landscape(client,write_headers,p1['id'],base['id']);r=client.post(f"/v1/scenario-landscapes/{land['visual_entity_id']}/scenarios",headers=write_headers,json={'data':{'scenario_entity_id':other['id'],'scenario_role':'alternative'}});assert r.status_code==422,r.text

def test_dimension_source_binding_and_uncertainty_validation(client,write_headers):
    p=_project(client,write_headers);pid=p['id'];base=_scenario(client,write_headers,pid,'Base');land=_landscape(client,write_headers,pid,base['id']);lid=land['visual_entity_id']
    model=_research(client,write_headers,'model','Model',{'project_entity_id':pid,'model_kind':'simulation','execution_target':'lab'});param=_research(client,write_headers,'parameter','Carbon price',{'model_entity_id':model['id'],'name':'carbon_price','data_type':'number','unit':'USD/tCO2e','default_value':{'value':50}})
    d=client.post(f'/v1/scenario-landscapes/{lid}/dimensions',headers=write_headers,json={'data':{'dimension_key':'carbon-price','dimension_kind':'parameter','source_entity_id':param['id'],'label':'Carbon price','unit':'USD/tCO2e'}});assert d.status_code==200,d.text
    bad=client.post(f'/v1/scenario-landscapes/{lid}/values',headers=write_headers,json={'data':{'scenario_entity_id':base['id'],'dimension_id':d.json()['id'],'numeric_value':50,'lower_bound':70,'upper_bound':40}});assert bad.status_code==422,bad.text

def test_saved_view_bundle_and_compile_renderer(client,write_headers):
    p=_project(client,write_headers);pid=p['id'];base=_scenario(client,write_headers,pid,'Base');alt=_scenario(client,write_headers,pid,'Alternative');land=_landscape(client,write_headers,pid,base['id']);lid=land['visual_entity_id'];client.post(f'/v1/scenario-landscapes/{lid}/scenarios',headers=write_headers,json={'data':{'scenario_entity_id':alt['id'],'scenario_role':'alternative'}})
    d=client.post(f'/v1/scenario-landscapes/{lid}/dimensions',headers=write_headers,json={'data':{'dimension_key':'cost','dimension_kind':'metric','label':'Cost','unit':'USD'}}).json();v=client.post(f'/v1/scenario-landscapes/{lid}/views',headers=write_headers,json={'data':{'view_key':'cost-view','name':'Cost view','scenario_ids':[base['id'],alt['id']],'dimension_ids':[d['id']],'layout_intent':{'family':'scatter'}}});assert v.status_code==200,v.text
    spec=client.post(f'/v1/scenario-landscapes/{lid}/compile-specification',headers=write_headers,json={'spec_key':'comparison','spec_kind':'chart','created_by':'tester'});assert spec.status_code==200,spec.text;body=spec.json();assert body['metadata_json']['scenario_landscape_v233'] is True and body['metadata_json']['scenario_execution_by_core'] is False
    resolved=client.post(f"/v1/visualization/specifications/{body['id']}/resolve",headers=write_headers,json={'created_by':'tester'});assert resolved.status_code==200,resolved.text;assert resolved.json()['resolved_renderer_key'] in {'contract.vega-lite','contract.plotly','contract.d3'} and resolved.json()['execution_performed'] is False
    bundle=client.get(f'/v1/scenario-landscapes/{lid}/bundle').json();assert len(bundle['scenarios'])==2 and bundle['views'][0]['view_key']=='cost-view'

def test_validate_no_execution_or_ranking(client,write_headers):
    p=_project(client,write_headers);base=_scenario(client,write_headers,p['id'],'Base');land=_landscape(client,write_headers,p['id'],base['id']);val=client.get(f"/v1/scenario-landscapes/{land['visual_entity_id']}/validate").json();assert val['valid'] is True;assert val['structural_only'] is True and val['scenario_execution_performed'] is False and val['model_execution_performed'] is False and val['ranking_performed'] is False and val['optimization_performed'] is False

def test_public_api_hides_private_landscapes(client,write_headers):
    p=_project(client,write_headers);base=_scenario(client,write_headers,p['id'],'Base');pub=_landscape(client,write_headers,p['id'],base['id'],'public'); priv_r=client.post('/v1/scenario-landscapes',headers=write_headers,json={'name':'Private futures','visibility':'private','project_entity_id':p['id'],'baseline_scenario_entity_id':base['id'],'comparison_mode':'baseline-relative','landscape_state':'draft','dimension_policy':'mixed'}); assert priv_r.status_code==200,priv_r.text; priv=priv_r.json();key=_public_key(client,write_headers);headers={'Authorization':f'Bearer {key}'};ready=client.get('/api/v1/scenario-landscapes/readiness',headers=headers);assert ready.status_code==200,ready.text;listed=client.get('/api/v1/scenario-landscapes',headers=headers);assert listed.status_code==200,listed.text;ids={x['visual_entity_id'] for x in listed.json()['data']};assert pub['visual_entity_id'] in ids and priv['visual_entity_id'] not in ids
