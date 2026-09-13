from __future__ import annotations

def _research(client, headers, object_type, name, attributes):
    r=client.post('/v1/research-objects',headers=headers,json={'object_type':object_type,'name':name,'slug':name.lower().replace(' ','-'),'visibility':'public','attributes':attributes})
    assert r.status_code==200,r.text; return r.json()

def _project(client,h,name='Compute project'):
    return _research(client,h,'research-project',name,{'research_question':'Compare scenarios'})

def _model(client,h,p,name='Compute model',target='lab'):
    return _research(client,h,'model',name,{'project_entity_id':p['id'],'model_kind':'simulation','execution_target':target,'specification':{},'assumptions':[],'equations':[]})

def _version(client,h,m,name='Compute model v1'):
    return _research(client,h,'model-version',name,{'model_entity_id':m['id'],'version_label':'v1','specification':{'kind':'test'},'immutable':True})

def _scenario(client,h,p,name='Baseline'):
    return _research(client,h,'scenario',name,{'project_entity_id':p['id'],'scenario_state':'ready','parameter_values':{'demand':100},'assumptions':[]})

def _parameter(client,h,m):
    return _research(client,h,'parameter','Demand parameter',{'model_entity_id':m['id'],'name':'demand','data_type':'number','unit':'MW','default_value':{'value':100},'bounds':{'min':0,'max':500}})

def _plan(client,h,p,m,v,visibility='public'):
    r=client.post('/v1/scenario-compute/plans',headers=h,json={'plan_key':'plan-'+p['id'][-8:],'name':'Scenario plan','visibility':visibility,'project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'execution_product':'lab','execution_contract':{'product':'lab','action':'execute-scenario'}})
    assert r.status_code==200,r.text; return r.json()

def _public_key(client,h):
    app=client.post('/v1/developer/applications',headers=h,json={'name':'Scenario SDK','owner_name':'Tester','owner_email':'scenario-sdk@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read public scenario compute metadata.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    assert app.status_code in (200,201),app.text
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=h,json={'label':'Scenario compute','scopes':['data:read'],'created_by':'admin'})
    assert issued.status_code in (200,201),issued.text
    return issued.json()['api_key']

def test_health_migration_and_readiness(client):
    h=client.get('/health').json(); assert h['version']=='2.38.0' and h['scenario_compute_engine'] is True
    r=client.get('/v1/scenario-compute/readiness'); assert r.status_code==200,r.text
    d=r.json(); assert d['migration_0038_applied'] is True and d['orchestration_by_core'] is True
    assert d['numerical_computation_by_core'] is False and d['arbitrary_code_execution_by_core'] is False

def test_plan_case_prepare_idempotent_manifest(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p);v=_version(client,write_headers,m);_parameter(client,write_headers,m);s=_scenario(client,write_headers,p);plan=_plan(client,write_headers,p,m,v)
    c=client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'baseline','scenario_entity_id':s['id'],'comparison_role':'baseline','parameter_overrides':{'demand':120},'expected_outputs':['cost']}}); assert c.status_code==200,c.text
    first=client.post(f"/v1/scenario-compute/plans/{plan['id']}/prepare",headers=write_headers,json={'submitted_by':'tester'}); assert first.status_code==200,first.text
    second=client.post(f"/v1/scenario-compute/plans/{plan['id']}/prepare",headers=write_headers,json={'submitted_by':'tester'}); assert second.status_code==200,second.text
    a=first.json()['prepared'][0]; b=second.json()['prepared'][0]; assert a['id']==b['id'] and a['request_hash']==b['request_hash']
    assert a['input_manifest_json']['parameter_values']['demand']==120 and a['input_manifest_json']['core_execution'] is False

def test_parameter_bound_validation(client,write_headers):
    p=_project(client,write_headers,'Bounds project');m=_model(client,write_headers,p,'Bounds model');v=_version(client,write_headers,m,'Bounds v1');_parameter(client,write_headers,m);s=_scenario(client,write_headers,p,'Bounds scenario');plan=_plan(client,write_headers,p,m,v)
    r=client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'bad','scenario_entity_id':s['id'],'parameter_overrides':{'demand':999}}}); assert r.status_code==422,r.text

def test_cross_project_scenario_rejected(client,write_headers):
    p1=_project(client,write_headers,'Project one');m=_model(client,write_headers,p1,'Model one');v=_version(client,write_headers,m,'Model one v1');p2=_project(client,write_headers,'Project two');s=_scenario(client,write_headers,p2,'Foreign scenario');plan=_plan(client,write_headers,p1,m,v)
    r=client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'foreign','scenario_entity_id':s['id']}}); assert r.status_code==422,r.text

def test_attempt_cannot_claim_core_execution(client,write_headers):
    p=_project(client,write_headers,'Attempt project');m=_model(client,write_headers,p,'Attempt model');v=_version(client,write_headers,m,'Attempt v1');s=_scenario(client,write_headers,p,'Attempt scenario');plan=_plan(client,write_headers,p,m,v);client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'a','scenario_entity_id':s['id']}});req=client.post(f"/v1/scenario-compute/plans/{plan['id']}/prepare",headers=write_headers,json={}).json()['prepared'][0]
    bad=client.post(f"/v1/scenario-compute/requests/{req['id']}/attempts",headers=write_headers,json={'data':{'attempt_state':'running','executor_product':'lab','executed_by_core':True}}); assert bad.status_code==422,bad.text
    ok=client.post(f"/v1/scenario-compute/requests/{req['id']}/attempts",headers=write_headers,json={'data':{'attempt_state':'running','executor_product':'lab','external_execution_id':'lab-123'}}); assert ok.status_code==200,ok.text

def test_model_run_and_result_binding(client,write_headers):
    p=_project(client,write_headers,'Binding project');m=_model(client,write_headers,p,'Binding model');v=_version(client,write_headers,m,'Binding v1');s=_scenario(client,write_headers,p,'Binding scenario');plan=_plan(client,write_headers,p,m,v);client.post(f"/v1/scenario-compute/plans/{plan['id']}/cases",headers=write_headers,json={'data':{'case_key':'bind','scenario_entity_id':s['id']}});req=client.post(f"/v1/scenario-compute/plans/{plan['id']}/prepare",headers=write_headers,json={}).json()['prepared'][0]
    run=_research(client,write_headers,'model-run','External run',{'model_version_entity_id':v['id'],'scenario_entity_id':s['id'],'executor_product':'lab','run_status':'completed','parameter_values':{}})
    br=client.post(f"/v1/scenario-compute/requests/{req['id']}/bind-run",headers=write_headers,json={'model_run_entity_id':run['id']}); assert br.status_code==200,br.text
    result=_research(client,write_headers,'result','Run result',{'model_run_entity_id':run['id'],'result_kind':'summary','value':{'value':42},'quality_status':'unreviewed'})
    rr=client.post(f"/v1/scenario-compute/requests/{req['id']}/results",headers=write_headers,json={'data':{'result_entity_id':result['id'],'output_key':'summary','binding_role':'primary'}}); assert rr.status_code==200,rr.text
    bundle=client.get(f"/v1/scenario-compute/plans/{plan['id']}/bundle").json(); assert bundle['result_bindings'][0]['result_entity_id']==result['id']

def test_plan_requires_immutable_model_version(client,write_headers):
    p=_project(client,write_headers,'Mutable project');m=_model(client,write_headers,p,'Mutable model');v=_research(client,write_headers,'model-version','Mutable version',{'model_entity_id':m['id'],'version_label':'mutable','specification':{},'immutable':False})
    r=client.post('/v1/scenario-compute/plans',headers=write_headers,json={'plan_key':'mutable','name':'Mutable','project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'execution_product':'lab'}); assert r.status_code==422,r.text

def test_public_api_hides_private_plans(client,write_headers):
    p=_project(client,write_headers,'Public project');m=_model(client,write_headers,p,'Public model');v=_version(client,write_headers,m,'Public v1');pub=_plan(client,write_headers,p,m,v,'public')
    p2=_project(client,write_headers,'Private project');m2=_model(client,write_headers,p2,'Private model');v2=_version(client,write_headers,m2,'Private v1');priv=_plan(client,write_headers,p2,m2,v2,'private')
    key=_public_key(client,write_headers);headers={'Authorization':f'Bearer {key}'}
    ready=client.get('/api/v1/scenario-compute/readiness',headers=headers); assert ready.status_code==200,ready.text
    listed=client.get('/api/v1/scenario-compute/plans',headers=headers); assert listed.status_code==200,listed.text
    ids={x['id'] for x in listed.json()['data']}; assert pub['id'] in ids and priv['id'] not in ids
