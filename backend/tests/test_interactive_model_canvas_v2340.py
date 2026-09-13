from __future__ import annotations
from app.migrations import MIGRATIONS


def _research(client,h,object_type,name,attrs,visibility='public'):
    r=client.post('/v1/research-objects',headers=h,json={'object_type':object_type,'name':name,'visibility':visibility,'attributes':attrs})
    assert r.status_code==200,r.text
    return r.json()


def _project(client,h):
    return _research(client,h,'research-project','Canvas project',{'research_question':'Explore model interactions'})


def _model(client,h,pid):
    return _research(client,h,'model','Energy model',{'project_entity_id':pid,'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]})


def _canvas(client,h,pid,mid,visibility='public'):
    r=client.post('/v1/model-canvases',headers=h,json={'name':'Energy model canvas','slug':f'energy-model-canvas-{visibility}','visibility':visibility,'project_entity_id':pid,'model_entity_id':mid,'canvas_state':'draft','interaction_mode':'inspect-configure','execution_target':'external','assumptions':['Execution remains external'],'metadata':{'v234':True}})
    assert r.status_code==200,r.text
    return r.json()


def _public_key(client,h):
    app=client.post('/v1/developer/applications',headers=h,json={'name':'Model Canvas Test','owner_name':'Tester','owner_email':'canvas@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read public model canvases.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    assert app.status_code in (200,201),app.text
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=h,json={'label':'Model canvas','scopes':['data:read'],'created_by':'admin'})
    assert issued.status_code in (200,201),issued.text
    return issued.json()['api_key']


def test_v234_health_migration_and_readiness(client):
    assert any(v=='0037' for v,_ in MIGRATIONS)
    health=client.get('/health').json()
    assert health['version']=='2.37.0' and health['interactive_model_canvas'] is True
    ready=client.get('/v1/model-canvases/readiness').json()
    assert ready['release']=='2.37.0' and ready['migration_0037_applied'] is True
    assert ready['visual_kind']=='model-canvas' and ready['research_models_reused'] is True
    assert ready['model_execution_by_core'] is False and ready['numerical_computation_by_core'] is False


def test_model_bound_nodes_edges_controls_and_validation(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id'])
    var=_research(client,write_headers,'variable','Demand',{'model_entity_id':m['id'],'symbol':'D','role':'input','data_type':'number','unit':'MW'})
    param=_research(client,write_headers,'parameter','Efficiency',{'model_entity_id':m['id'],'name':'efficiency','data_type':'number','unit':'percent','default_value':{'value':80},'bounds':{'min':0,'max':100}})
    c=_canvas(client,write_headers,p['id'],m['id']);cid=c['visual_entity_id']
    n1=client.post(f'/v1/model-canvases/{cid}/nodes',headers=write_headers,json={'data':{'node_key':'demand','node_kind':'input','semantic_role':'input','bound_entity_id':var['id'],'label':'Demand','unit':'MW'}});assert n1.status_code==200,n1.text
    n2=client.post(f'/v1/model-canvases/{cid}/nodes',headers=write_headers,json={'data':{'node_key':'efficiency','node_kind':'parameter','semantic_role':'parameter','bound_entity_id':param['id'],'label':'Efficiency','unit':'percent'}});assert n2.status_code==200,n2.text
    edge=client.post(f'/v1/model-canvases/{cid}/edges',headers=write_headers,json={'data':{'source_node_id':n1.json()['id'],'target_node_id':n2.json()['id'],'edge_kind':'dependency','directed':True}});assert edge.status_code==200,edge.text
    ctrl=client.post(f'/v1/model-canvases/{cid}/controls',headers=write_headers,json={'data':{'control_key':'efficiency-slider','control_kind':'slider','node_id':n2.json()['id'],'bound_entity_id':param['id'],'label':'Efficiency','data_type':'number','unit':'percent','default_value':80,'bounds':{'min':0,'max':100,'step':1},'handoff':{'product':'lab','action':'request-run'}}});assert ctrl.status_code==200,ctrl.text
    val=client.get(f'/v1/model-canvases/{cid}/validate').json();assert val['valid'] is True and val['structural_only'] is True;assert val['model_execution_performed'] is False and val['numerical_computation_performed'] is False


def test_core_execution_control_is_rejected(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id']);c=_canvas(client,write_headers,p['id'],m['id']);cid=c['visual_entity_id']
    r=client.post(f'/v1/model-canvases/{cid}/controls',headers=write_headers,json={'data':{'control_key':'run','control_kind':'action-request','label':'Run','data_type':'boolean','handoff':{'execute_by_core':True}}})
    assert r.status_code==422,r.text


def test_immutable_states_and_scenario_binding(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id']);sc=_research(client,write_headers,'scenario','High demand',{'project_entity_id':p['id'],'scenario_state':'ready','parameter_values':{},'assumptions':[]});c=_canvas(client,write_headers,p['id'],m['id']);cid=c['visual_entity_id']
    payload={'data':{'state_key':'high-demand','name':'High demand state','scenario_entity_id':sc['id'],'values':{'efficiency':80},'provenance':{'source':'user'},'created_by':'tester'}}
    first=client.post(f'/v1/model-canvases/{cid}/states',headers=write_headers,json=payload);assert first.status_code==200,first.text;assert first.json()['immutable'] is True and len(first.json()['state_hash'])==64
    second=client.post(f'/v1/model-canvases/{cid}/states',headers=write_headers,json=payload);assert second.status_code==409,second.text


def test_compile_visualization_spec_and_resolve_renderer(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id']);c=_canvas(client,write_headers,p['id'],m['id']);cid=c['visual_entity_id']
    spec=client.post(f'/v1/model-canvases/{cid}/compile-specification',headers=write_headers,json={'spec_key':'interactive','spec_kind':'diagram','created_by':'tester'});assert spec.status_code==200,spec.text
    body=spec.json();assert body['metadata_json']['interactive_model_canvas_v234'] is True and body['metadata_json']['model_execution_by_core'] is False
    resolved=client.post(f"/v1/visualization/specifications/{body['id']}/resolve",headers=write_headers,json={'created_by':'tester'});assert resolved.status_code==200,resolved.text
    assert resolved.json()['resolved_renderer_key']=='contract.d3' and resolved.json()['execution_performed'] is False


def test_saved_view_and_bundle(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id']);c=_canvas(client,write_headers,p['id'],m['id']);cid=c['visual_entity_id']
    bundle=client.get(f'/v1/model-canvases/{cid}/bundle').json();model_node=bundle['nodes'][0]
    view=client.post(f'/v1/model-canvases/{cid}/views',headers=write_headers,json={'data':{'view_key':'overview','name':'Overview','node_ids':[model_node['id']],'edge_ids':[],'control_ids':[],'layout_intent':{'family':'canvas'}}});assert view.status_code==200,view.text
    bundle=client.get(f'/v1/model-canvases/{cid}/bundle').json();assert bundle['canvas']['model_entity_id']==m['id'] and bundle['views'][0]['view_key']=='overview' and bundle['validation']['valid'] is True


def test_public_api_hides_private_canvases(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p['id']);pub=_canvas(client,write_headers,p['id'],m['id'],'public');priv=_canvas(client,write_headers,p['id'],m['id'],'private');key=_public_key(client,write_headers);headers={'Authorization':f'Bearer {key}'}
    ready=client.get('/api/v1/model-canvases/readiness',headers=headers);assert ready.status_code==200,ready.text
    listed=client.get('/api/v1/model-canvases',headers=headers);assert listed.status_code==200,listed.text
    ids={x['visual_entity_id'] for x in listed.json()['data']};assert pub['visual_entity_id'] in ids and priv['visual_entity_id'] not in ids
