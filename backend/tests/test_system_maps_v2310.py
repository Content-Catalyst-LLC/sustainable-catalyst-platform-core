from __future__ import annotations
from app.migrations import MIGRATIONS


def _create_map(client, write_headers, name='Energy system map', visibility='public'):
    r=client.post('/v1/system-maps',headers=write_headers,json={
        'name':name,'visibility':visibility,'reasoning_purpose':'explain','system_purpose':'understand-system',
        'perspective':'socio-technical','map_state':'draft','boundary_statement':'Energy system under study',
        'assumptions':['Boundaries are explicit'],'metadata':{'v231':True},'created_by':'tester'
    })
    assert r.status_code==200,r.text
    return r.json()


def _element(client,write_headers,map_id,key,label,role='actor'):
    r=client.post(f'/v1/visual-reasoning/objects/{map_id}/elements',headers=write_headers,json={'data':{
        'element_key':key,'element_kind':'node','semantic_role':role,'label':label,
        'uncertainty':{},'provenance':{},'metadata':{}
    }})
    assert r.status_code==200,r.text
    return r.json()


def _public_key(client,write_headers):
    app=client.post('/v1/developer/applications',headers=write_headers,json={
        'name':'System Maps Test','owner_name':'Tester','owner_email':'system-maps@example.com','organization':'Test',
        'website_url':'https://example.com','use_case':'Read public system maps.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    assert app.status_code in (200,201),app.text
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=write_headers,json={'label':'System maps','scopes':['data:read'],'created_by':'admin'})
    assert issued.status_code in (200,201),issued.text
    return issued.json()['api_key']


def test_v2310_health_migration_and_readiness(client):
    assert any(v=='0034' for v,_ in MIGRATIONS)
    health=client.get('/health').json()
    assert health['version']=='2.53.0'
    assert health['system_maps'] is True
    ready=client.get('/v1/system-maps/readiness').json()
    assert ready['release']=='2.53.0'
    assert ready['migration_0034_applied'] is True
    assert ready['visual_kind']=='system-map'
    assert ready['renderer_neutral'] is True
    assert ready['layout_engine_in_core'] is False
    assert ready['causal_inference_by_core'] is False
    assert ready['automatic_truth_promotion'] is False


def test_system_map_boundaries_domains_membership_and_validation(client,write_headers):
    sm=_create_map(client,write_headers); mid=sm['visual_entity_id']
    assert sm['visual_reasoning']['visual_kind']=='system-map'
    boundary=client.post(f'/v1/system-maps/{mid}/boundaries',headers=write_headers,json={'data':{'boundary_key':'scope','boundary_kind':'included','name':'Study scope','criteria':{'rule':'explicit'}}})
    assert boundary.status_code==200,boundary.text
    domain=client.post(f'/v1/system-maps/{mid}/domains',headers=write_headers,json={'data':{'domain_key':'supply','name':'Supply'}})
    assert domain.status_code==200,domain.text
    e=_element(client,write_headers,mid,'grid','Electric grid')
    mem=client.post(f'/v1/system-maps/{mid}/memberships',headers=write_headers,json={'data':{'domain_id':domain.json()['id'],'element_id':e['id'],'membership_role':'primary'}})
    assert mem.status_code==200,mem.text
    val=client.get(f'/v1/system-maps/{mid}/validate').json()
    assert val['valid'] is True
    assert val['structural_only'] is True
    assert val['causal_inference_performed'] is False
    assert val['counts']['elements']==1
    assert val['counts']['domains']==1
    assert 'system_boundary_not_explicit' not in val['warnings']


def test_cross_map_membership_is_rejected(client,write_headers):
    a=_create_map(client,write_headers,'A'); b=_create_map(client,write_headers,'B')
    d=client.post(f"/v1/system-maps/{a['visual_entity_id']}/domains",headers=write_headers,json={'data':{'domain_key':'a','name':'A'}}).json()
    e=_element(client,write_headers,b['visual_entity_id'],'b-node','B node')
    r=client.post(f"/v1/system-maps/{a['visual_entity_id']}/memberships",headers=write_headers,json={'data':{'domain_id':d['id'],'element_id':e['id']}})
    assert r.status_code==422,r.text


def test_compile_system_map_to_v230_spec_and_resolve_renderer(client,write_headers):
    sm=_create_map(client,write_headers); mid=sm['visual_entity_id']
    _element(client,write_headers,mid,'producer','Producer','actor')
    _element(client,write_headers,mid,'resource','Resource','stock')
    spec=client.post(f'/v1/system-maps/{mid}/compile-specification',headers=write_headers,json={'spec_key':'primary','created_by':'tester'})
    assert spec.status_code==200,spec.text
    body=spec.json()
    assert body['spec_kind']=='diagram'
    assert body['metadata_json']['system_map_v231'] is True
    assert body['layout_constraints_json']['runtime_owns_layout'] is True
    resolved=client.post(f"/v1/visualization/specifications/{body['id']}/resolve",headers=write_headers,json={'created_by':'tester'})
    assert resolved.status_code==200,resolved.text
    assert resolved.json()['resolved_renderer_key']=='contract.d3'
    assert resolved.json()['execution_performed'] is False


def test_saved_view_and_bundle(client,write_headers):
    sm=_create_map(client,write_headers); mid=sm['visual_entity_id']
    r=client.post(f'/v1/system-maps/{mid}/views',headers=write_headers,json={'data':{'view_key':'overview','name':'Overview','lens':{'focus':'all'},'filters':{},'highlights':[],'layout_intent':{'direction':'left-to-right'}}})
    assert r.status_code==200,r.text
    bundle=client.get(f'/v1/system-maps/{mid}/bundle')
    assert bundle.status_code==200,bundle.text
    assert bundle.json()['views'][0]['view_key']=='overview'
    assert bundle.json()['visual_reasoning']['object']['attributes']['visual_kind']=='system-map'


def test_public_api_hides_private_system_maps(client,write_headers):
    pub=_create_map(client,write_headers,'Public','public'); priv=_create_map(client,write_headers,'Private','private')
    key=_public_key(client,write_headers); headers={'Authorization':f'Bearer {key}'}
    ready=client.get('/api/v1/system-maps/readiness',headers=headers)
    assert ready.status_code==200,ready.text
    listed=client.get('/api/v1/system-maps',headers=headers)
    assert listed.status_code==200,listed.text
    ids={x['visual_entity_id'] for x in listed.json()['data']}
    assert pub['visual_entity_id'] in ids
    assert priv['visual_entity_id'] not in ids
