from __future__ import annotations
from app.migrations import MIGRATIONS


def _create_map(client, write_headers, name='Energy flow map', visibility='public', quantity_mode='quantitative'):
    r=client.post('/v1/flow-maps',headers=write_headers,json={
        'name':name,'visibility':visibility,'reasoning_purpose':'explain','flow_purpose':'trace',
        'flow_domain':'energy','map_state':'draft','quantity_mode':quantity_mode,'default_unit':'MWh',
        'time_basis':'interval','conservation_policy':'advisory','assumptions':['Units are explicit'],
        'metadata':{'v232':True},'created_by':'tester'})
    assert r.status_code==200,r.text
    return r.json()


def _element(client,write_headers,map_id,key,label,role='actor'):
    r=client.post(f'/v1/visual-reasoning/objects/{map_id}/elements',headers=write_headers,json={'data':{
        'element_key':key,'element_kind':'node','semantic_role':role,'label':label,
        'uncertainty':{},'provenance':{},'metadata':{}}})
    assert r.status_code==200,r.text
    return r.json()


def _public_key(client,write_headers):
    app=client.post('/v1/developer/applications',headers=write_headers,json={
        'name':'Flow Maps Test','owner_name':'Tester','owner_email':'flow-maps@example.com','organization':'Test',
        'website_url':'https://example.com','use_case':'Read public flow maps.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    assert app.status_code in (200,201),app.text
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=write_headers,json={'label':'Flow maps','scopes':['data:read'],'created_by':'admin'})
    assert issued.status_code in (200,201),issued.text
    return issued.json()['api_key']


def test_v2320_health_migration_and_readiness(client):
    assert any(v=='0035' for v,_ in MIGRATIONS)
    health=client.get('/health').json()
    assert health['version']=='2.36.1.2'
    assert health['flow_maps'] is True
    ready=client.get('/v1/flow-maps/readiness').json()
    assert ready['release']=='2.36.1.2'
    assert ready['migration_0035_applied'] is True
    assert ready['visual_kind']=='flow-map'
    assert ready['flow_relations_reused'] is True
    assert ready['unit_conversion_by_core'] is False
    assert ready['simulation_by_core'] is False
    assert ready['automatic_conservation_claim'] is False
    assert ready['automatic_truth_promotion'] is False


def test_flow_channels_relation_binding_and_balance(client,write_headers):
    fm=_create_map(client,write_headers); mid=fm['visual_entity_id']
    source=_element(client,write_headers,mid,'solar','Solar farm','input')
    target=_element(client,write_headers,mid,'grid','Grid','stock')
    ch=client.post(f'/v1/flow-maps/{mid}/channels',headers=write_headers,json={'data':{'channel_key':'electricity','name':'Electricity','flow_kind':'energy','unit':'MWh'}})
    assert ch.status_code==200,ch.text
    flow=client.post(f'/v1/flow-maps/{mid}/flows',headers=write_headers,json={'data':{
        'flow_key':'solar-grid','source_element_id':source['id'],'target_element_id':target['id'],'channel_id':ch.json()['id'],
        'quantity_kind':'amount','quantity_value':125.5,'unit':'MWh','flow_status':'observed','provenance':{'source':'meter'}}})
    assert flow.status_code==200,flow.text
    body=flow.json(); assert body['source_element_id']==source['id'] and body['target_element_id']==target['id']
    bundle=client.get(f'/v1/flow-maps/{mid}/bundle').json()
    rel=next(r for r in bundle['visual_reasoning']['relations'] if r['id']==body['relation_id'])
    assert rel['relation_kind']=='flow' and rel['direction']=='directed'
    bal=client.get(f'/v1/flow-maps/{mid}/balance').json()
    assert bal['balances_by_unit']['MWh'][source['id']]['outgoing']==125.5
    assert bal['balances_by_unit']['MWh'][target['id']]['incoming']==125.5
    assert bal['unit_conversion_performed'] is False and bal['conservation_claim'] is False


def test_cross_map_references_rejected(client,write_headers):
    a=_create_map(client,write_headers,'A'); b=_create_map(client,write_headers,'B')
    a_id=a['visual_entity_id']; b_id=b['visual_entity_id']
    a1=_element(client,write_headers,a_id,'a1','A1'); b1=_element(client,write_headers,b_id,'b1','B1')
    r=client.post(f'/v1/flow-maps/{a_id}/flows',headers=write_headers,json={'data':{'flow_key':'bad','source_element_id':a1['id'],'target_element_id':b1['id']}})
    assert r.status_code==422,r.text
    ch=client.post(f'/v1/flow-maps/{b_id}/channels',headers=write_headers,json={'data':{'channel_key':'b','name':'B'}}).json()
    r=client.post(f'/v1/flow-maps/{a_id}/flows',headers=write_headers,json={'data':{'flow_key':'bad2','source_element_id':a1['id'],'target_element_id':a1['id'],'channel_id':ch['id']}})
    assert r.status_code==422,r.text


def test_multi_unit_validation_no_automatic_conversion(client,write_headers):
    fm=_create_map(client,write_headers); mid=fm['visual_entity_id']
    a=_element(client,write_headers,mid,'a','A'); b=_element(client,write_headers,mid,'b','B'); c=_element(client,write_headers,mid,'c','C')
    for key,src,dst,value,unit in [('mwh',a,b,10,'MWh'),('gj',b,c,3.6,'GJ')]:
        r=client.post(f'/v1/flow-maps/{mid}/flows',headers=write_headers,json={'data':{'flow_key':key,'source_element_id':src['id'],'target_element_id':dst['id'],'quantity_kind':'amount','quantity_value':value,'unit':unit}})
        assert r.status_code==200,r.text
    val=client.get(f'/v1/flow-maps/{mid}/validate').json()
    assert 'multiple_units_present_no_automatic_conversion' in val['warnings']
    bal=client.get(f'/v1/flow-maps/{mid}/balance').json()
    assert set(bal['balances_by_unit'])=={'MWh','GJ'} and bal['unit_conversion_performed'] is False


def test_node_state_saved_view_and_bundle(client,write_headers):
    fm=_create_map(client,write_headers); mid=fm['visual_entity_id']; node=_element(client,write_headers,mid,'battery','Battery','stock')
    ch=client.post(f'/v1/flow-maps/{mid}/channels',headers=write_headers,json={'data':{'channel_key':'power','name':'Power','flow_kind':'energy','unit':'MWh'}}).json()
    state=client.post(f'/v1/flow-maps/{mid}/node-states',headers=write_headers,json={'data':{'element_id':node['id'],'state_key':'soc','state_kind':'stock','quantity_value':40,'unit':'MWh'}})
    assert state.status_code==200,state.text
    view=client.post(f'/v1/flow-maps/{mid}/views',headers=write_headers,json={'data':{'view_key':'energy','name':'Energy','channel_ids':[ch['id']],'filters':{},'time_window':{},'layout_intent':{'direction':'left-to-right'}}})
    assert view.status_code==200,view.text
    bundle=client.get(f'/v1/flow-maps/{mid}/bundle').json()
    assert bundle['node_states'][0]['state_key']=='soc' and bundle['views'][0]['view_key']=='energy'


def test_compile_flow_map_network_and_map_specs_resolve_renderer(client,write_headers):
    fm=_create_map(client,write_headers); mid=fm['visual_entity_id']; _element(client,write_headers,mid,'a','A'); _element(client,write_headers,mid,'b','B')
    network=client.post(f'/v1/flow-maps/{mid}/compile-specification',headers=write_headers,json={'spec_key':'network','spec_kind':'network','created_by':'tester'})
    assert network.status_code==200,network.text
    n=network.json(); assert n['metadata_json']['flow_map_v232'] is True and n['layout_constraints_json']['runtime_owns_layout'] is True
    nr=client.post(f"/v1/visualization/specifications/{n['id']}/resolve",headers=write_headers,json={'created_by':'tester'})
    assert nr.status_code==200,nr.text; assert nr.json()['resolved_renderer_key']=='contract.d3'; assert nr.json()['execution_performed'] is False
    mapped=client.post(f'/v1/flow-maps/{mid}/compile-specification',headers=write_headers,json={'spec_key':'geo','spec_kind':'map','created_by':'tester'})
    assert mapped.status_code==200,mapped.text
    mr=client.post(f"/v1/visualization/specifications/{mapped.json()['id']}/resolve",headers=write_headers,json={'created_by':'tester'})
    assert mr.status_code==200,mr.text; assert mr.json()['resolved_renderer_key']=='contract.maplibre'; assert mr.json()['execution_performed'] is False


def test_public_api_hides_private_flow_maps(client,write_headers):
    pub=_create_map(client,write_headers,'Public','public'); priv=_create_map(client,write_headers,'Private','private')
    key=_public_key(client,write_headers); headers={'Authorization':f'Bearer {key}'}
    ready=client.get('/api/v1/flow-maps/readiness',headers=headers); assert ready.status_code==200,ready.text
    listed=client.get('/api/v1/flow-maps',headers=headers); assert listed.status_code==200,listed.text
    ids={x['visual_entity_id'] for x in listed.json()['data']}
    assert pub['visual_entity_id'] in ids and priv['visual_entity_id'] not in ids
