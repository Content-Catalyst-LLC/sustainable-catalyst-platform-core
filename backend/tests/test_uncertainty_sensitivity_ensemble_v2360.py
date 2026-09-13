from __future__ import annotations

def _research(client,h,typ,name,attrs):
    rr=client.post('/v1/research-objects',headers=h,json={'object_type':typ,'name':name,'slug':name.lower().replace(' ','-'),'visibility':'public','attributes':attrs}); assert rr.status_code==200,rr.text; return rr.json()
def _project(c,h,n='UQ project'): return _research(c,h,'research-project',n,{'research_question':'Characterize uncertainty'})
def _model(c,h,p,n='UQ model'): return _research(c,h,'model',n,{'project_entity_id':p['id'],'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]})
def _version(c,h,m,n='UQ model v1'): return _research(c,h,'model-version',n,{'model_entity_id':m['id'],'version_label':'v1','specification':{},'immutable':True})
def _param(c,h,m,n='Demand parameter'): return _research(c,h,'parameter',n,{'model_entity_id':m['id'],'name':n.lower().replace(' ','_'),'data_type':'number','unit':'MW','default_value':{'value':100},'bounds':{'min':0,'max':500}})
def _scenario(c,h,p,n='Baseline scenario'): return _research(c,h,'scenario',n,{'project_entity_id':p['id'],'scenario_state':'ready','parameter_values':{},'assumptions':[]})
def _plan(c,h,p,m,v,n='uq-plan'):
    rr=c.post('/v1/scenario-compute/plans',headers=h,json={'plan_key':n+'-'+p['id'][-6:],'name':'UQ plan','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'execution_product':'lab'}); assert rr.status_code==200,rr.text; return rr.json()
def _pubkey(c,h):
    a=c.post('/v1/developer/applications',headers=h,json={'name':'UQ SDK','owner_name':'Tester','owner_email':'uq-sdk@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read uncertainty reasoning metadata.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'});assert a.status_code in (200,201),a.text
    k=c.post(f"/v1/developer/applications/{a.json()['id']}/credentials",headers=h,json={'label':'UQ read','scopes':['data:read'],'created_by':'admin'});assert k.status_code in (200,201),k.text;return k.json()['api_key']

def test_health_migration_and_readiness(client):
    h=client.get('/health').json();assert h['version']=='2.36.1' and h['uncertainty_sensitivity_ensemble_reasoning'] is True
    d=client.get('/v1/uncertainty-reasoning/readiness').json();assert d['migration_0039_applied'] is True and d['uncertainty_first_class'] is True
    assert d['monte_carlo_execution_by_core'] is True and d['ensemble_aggregation_by_core'] is True

def test_uncertainty_definition_and_bounds(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p);q=_param(client,write_headers,m)
    u=client.post('/v1/uncertainty-reasoning/uncertainty-definitions',headers=write_headers,json={'uncertainty_key':'demand-uq','name':'Demand uncertainty','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'target_entity_id':q['id'],'uncertainty_kind':'distribution','distribution_name':'triangular','unit':'MW','lower_bound':80,'upper_bound':140,'confidence_level':0.95,'parameters':{'mode':100},'provenance':{'source':'test'}});assert u.status_code==200,u.text
    assert u.json()['distribution_name']=='triangular'
    bad=client.post('/v1/uncertainty-reasoning/uncertainty-definitions',headers=write_headers,json={'uncertainty_key':'bad','name':'Bad','project_entity_id':p['id'],'target_entity_id':q['id'],'uncertainty_kind':'interval','lower_bound':2,'upper_bound':1});assert bad.status_code==422,bad.text

def test_sensitivity_factor_external_result_and_renderer(client,write_headers):
    p=_project(client,write_headers,'Sensitivity project');m=_model(client,write_headers,p,'Sensitivity model');v=_version(client,write_headers,m,'Sensitivity v1');q=_param(client,write_headers,m,'Load parameter');plan=_plan(client,write_headers,p,m,v,'sens')
    u=client.post('/v1/uncertainty-reasoning/uncertainty-definitions',headers=write_headers,json={'uncertainty_key':'load-uq','name':'Load uncertainty','project_entity_id':p['id'],'model_entity_id':m['id'],'target_entity_id':q['id'],'uncertainty_kind':'interval','lower_bound':90,'upper_bound':110}).json()
    s=client.post('/v1/uncertainty-reasoning/sensitivity-studies',headers=write_headers,json={'study_key':'study','name':'Sensitivity study','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'compute_plan_id':plan['id'],'method':'sobol','output_key':'cost','sampling_contract':{'sample_count':512,'seed':42}});assert s.status_code==200,s.text;sid=s.json()['visual_entity_id']
    f=client.post(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/factors',headers=write_headers,json={'data':{'factor_key':'load','parameter_entity_id':q['id'],'uncertainty_definition_id':u['id'],'lower_bound':90,'upper_bound':110}});assert f.status_code==200,f.text
    bad=client.post(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/results',headers=write_headers,json={'data':{'factor_id':f.json()['id'],'metric_kind':'sobol-first','output_key':'cost','value':{'value':0.4},'source_execution':{'calculated_by_core':True}}});assert bad.status_code==422,bad.text
    good=client.post(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/results',headers=write_headers,json={'data':{'factor_id':f.json()['id'],'metric_kind':'sobol-first','output_key':'cost','value':{'value':0.4},'source_execution':{'executor':'lab','run':'x'}}});assert good.status_code==200,good.text
    spec=client.post(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/compile-specification',headers=write_headers,json={'data':{}});assert spec.status_code==200,spec.text;assert spec.json()['renderer_resolution']['resolved_renderer_key']=='contract.vega-lite'
    val=client.get(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/validate').json();assert val['sensitivity_calculation_performed'] is False and val['counts']['results']==1

def test_cross_model_factor_rejected(client,write_headers):
    p=_project(client,write_headers,'Cross factor project');m1=_model(client,write_headers,p,'Model A');v1=_version(client,write_headers,m1,'Model A v1');m2=_model(client,write_headers,p,'Model B');q2=_param(client,write_headers,m2,'Foreign parameter')
    s=client.post('/v1/uncertainty-reasoning/sensitivity-studies',headers=write_headers,json={'study_key':'cross','name':'Cross','project_entity_id':p['id'],'model_entity_id':m1['id'],'model_version_entity_id':v1['id']}).json();sid=s['visual_entity_id']
    rr=client.post(f'/v1/uncertainty-reasoning/sensitivity-studies/{sid}/factors',headers=write_headers,json={'data':{'factor_key':'foreign','parameter_entity_id':q2['id']}});assert rr.status_code==422,rr.text

def test_ensemble_members_statistics_and_renderer(client,write_headers):
    p=_project(client,write_headers,'Ensemble project');m=_model(client,write_headers,p,'Ensemble model');v=_version(client,write_headers,m,'Ensemble v1');s=_scenario(client,write_headers,p,'Ensemble scenario');plan=_plan(client,write_headers,p,m,v,'ens')
    case=client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'member','scenario_entity_id':s['id']}}).json();req=client.post(f"/v1/scenario-compute/plans/{plan['id']}/prepare",headers=write_headers,json={}).json()['prepared'][0]
    run=_research(client,write_headers,'model-run','Ensemble run',{'model_version_entity_id':v['id'],'scenario_entity_id':s['id'],'executor_product':'lab','run_status':'completed','parameter_values':{}})
    e=client.post('/v1/uncertainty-reasoning/ensembles',headers=write_headers,json={'ensemble_key':'ensemble','name':'Ensemble','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'compute_plan_id':plan['id'],'weighting_policy':'explicit'});assert e.status_code==200,e.text;eid=e.json()['visual_entity_id']
    mem=client.post(f'/v1/uncertainty-reasoning/ensembles/{eid}/members',headers=write_headers,json={'data':{'member_key':'m1','scenario_entity_id':s['id'],'compute_case_id':case['id'],'compute_request_id':req['id'],'model_run_entity_id':run['id'],'weight':1.0}});assert mem.status_code==200,mem.text
    bad=client.post(f'/v1/uncertainty-reasoning/ensembles/{eid}/statistics',headers=write_headers,json={'data':{'statistic_key':'mean-cost','output_key':'cost','statistic_kind':'mean','value':{'value':10},'source_execution':{'calculated_by_core':True}}});assert bad.status_code==422,bad.text
    st=client.post(f'/v1/uncertainty-reasoning/ensembles/{eid}/statistics',headers=write_headers,json={'data':{'statistic_key':'mean-cost','output_key':'cost','statistic_kind':'mean','value':{'value':10},'source_execution':{'executor':'workbench'}}});assert st.status_code==200,st.text
    spec=client.post(f'/v1/uncertainty-reasoning/ensembles/{eid}/compile-specification',headers=write_headers,json={'data':{}});assert spec.status_code==200,spec.text;assert spec.json()['renderer_resolution']['resolved_renderer_key']=='contract.plotly'
    val=client.get(f'/v1/uncertainty-reasoning/ensembles/{eid}/validate').json();assert val['aggregation_performed'] is False and val['counts']['members']==1

def test_ensemble_rejects_incompatible_run(client,write_headers):
    p=_project(client,write_headers,'Run compatibility');m1=_model(client,write_headers,p,'Run Model A');v1=_version(client,write_headers,m1,'Run A v1');m2=_model(client,write_headers,p,'Run Model B');v2=_version(client,write_headers,m2,'Run B v1');s=_scenario(client,write_headers,p,'Run scenario');run=_research(client,write_headers,'model-run','Foreign run',{'model_version_entity_id':v2['id'],'scenario_entity_id':s['id'],'executor_product':'lab','run_status':'completed','parameter_values':{}})
    e=client.post('/v1/uncertainty-reasoning/ensembles',headers=write_headers,json={'ensemble_key':'run-check','name':'Run check','project_entity_id':p['id'],'model_entity_id':m1['id'],'model_version_entity_id':v1['id']}).json();eid=e['visual_entity_id']
    rr=client.post(f'/v1/uncertainty-reasoning/ensembles/{eid}/members',headers=write_headers,json={'data':{'member_key':'bad','model_run_entity_id':run['id']}});assert rr.status_code==422,rr.text

def test_public_api_hides_private_reasoning_objects(client,write_headers):
    p=_project(client,write_headers,'Public UQ project');m=_model(client,write_headers,p,'Public UQ model');v=_version(client,write_headers,m,'Public UQ v1');q=_param(client,write_headers,m,'Public parameter')
    client.post('/v1/uncertainty-reasoning/uncertainty-definitions',headers=write_headers,json={'uncertainty_key':'pub','name':'Public UQ','visibility':'public','project_entity_id':p['id'],'target_entity_id':q['id'],'uncertainty_kind':'interval'})
    client.post('/v1/uncertainty-reasoning/uncertainty-definitions',headers=write_headers,json={'uncertainty_key':'priv','name':'Private UQ','visibility':'private','project_entity_id':p['id'],'target_entity_id':q['id'],'uncertainty_kind':'interval'})
    pub=client.post('/v1/uncertainty-reasoning/sensitivity-studies',headers=write_headers,json={'study_key':'pub-study','name':'Public study','visibility':'public','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id']}).json();client.post('/v1/uncertainty-reasoning/sensitivity-studies',headers=write_headers,json={'study_key':'priv-study','name':'Private study','visibility':'private','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id']})
    key=_pubkey(client,write_headers);h={'Authorization':f'Bearer {key}'}
    u=client.get('/api/v1/uncertainty-reasoning/uncertainty-definitions',headers=h);assert u.status_code==200,u.text;assert {x['uncertainty_key'] for x in u.json()['data']}=={'pub'}
    studies=client.get('/api/v1/uncertainty-reasoning/sensitivity-studies',headers=h);assert studies.status_code==200,studies.text;assert pub['visual_entity_id'] in {x['visual_entity_id'] for x in studies.json()['data']}

def test_readiness_declares_non_execution_boundaries(client):
    d=client.get('/v1/uncertainty-reasoning/readiness').json();assert d['sampling_execution_by_core'] is True and d['sensitivity_calculation_by_core'] is True and d['ensemble_aggregation_by_core'] is True and d['automatic_probability_inference'] is False
