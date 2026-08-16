from datetime import datetime, timezone, timedelta

from app.models import LiveDataObservation

NOW=datetime(2026,8,14,tzinfo=timezone.utc)

def post_condition(client, headers, **overrides):
    payload={
        'country_code':'PSE','service_domain':'food','condition_kind':'access-status',
        'semantic_role':'operational-condition','status_value':'access-constrained',
        'observed_at':NOW.isoformat(),'publisher':'OCHA','evidence_class':'operational-reporting',
        'source_record_id':'food-1','public':True,
    }
    payload.update(overrides)
    r=client.post('/v1/humanitarian/conditions',headers=headers,json=payload)
    assert r.status_code==200,r.text
    return r.json()

def test_release_and_readiness(client):
    assert client.get('/health').json()['version']=='2.25.0'
    r=client.get('/v1/humanitarian/readiness'); assert r.status_code==200
    body=r.json(); assert body['release']=='2.25.0'; assert body['migration_0014_applied'] is True
    assert body['structured_source_materialization_only'] is True
    assert body['reliefweb_report_metadata_promoted_to_operational_claim'] is False
    assert body['synthetic_severity_scoring'] is False
    assert body['zero_records_mean_normal_conditions'] is False

def test_requested_service_domains_are_first_class(client):
    domains=set(client.get('/v1/humanitarian/readiness').json()['service_domains'])
    assert {'health','education','food','water','electricity','fuel','displacement','communications','shelter','humanitarian-access'} <= domains

def test_conditions_stay_separate_and_country_summary_has_no_synthetic_severity(client,write_headers):
    post_condition(client,write_headers)
    post_condition(client,write_headers,service_domain='electricity',condition_kind='interruption',status_value='service-unavailable',source_record_id='power-1')
    out=client.get('/v1/humanitarian/country/PSE/summary').json()
    assert out['records']==2; assert out['domains']['food']==1; assert out['domains']['electricity']==1
    assert out['synthetic_severity_score'] is None; assert out['automatic_legal_conclusion'] is False; assert out['automatic_causal_attribution'] is False

def test_structural_baseline_is_not_current_conditions_eligible(client,write_headers):
    out=post_condition(client,write_headers,service_domain='electricity',condition_kind='availability',semantic_role='structural-baseline',status_value=None,value_number=100,unit='percent',publisher='World Bank',evidence_class='harmonized-benchmark',source_record_id='wb-electricity-2024')
    assert out['current_conditions_eligible'] is False
    summary=client.get('/v1/humanitarian/country/PSE/summary').json()
    assert summary['structural_context_records']==1; assert summary['current_conditions_eligible_records']==0

def test_facility_link_requires_same_country(client,write_headers):
    f=client.post('/v1/facilities',headers=write_headers,json={'name':'Example Hospital','facility_type':'hospital','country_code':'PSE'}).json()
    out=post_condition(client,write_headers,service_domain='health',condition_kind='operational-status',status_value='partially-operational',facility_id=f['id'],source_record_id='hospital-status-1')
    assert out['facility_id']==f['id']
    other=client.post('/v1/facilities',headers=write_headers,json={'name':'Other School','facility_type':'school','country_code':'JOR'}).json()
    r=client.post('/v1/humanitarian/conditions',headers=write_headers,json={'country_code':'PSE','service_domain':'education','condition_kind':'operational-status','status_value':'closed','observed_at':NOW.isoformat(),'publisher':'Education Cluster','facility_id':other['id']})
    assert r.status_code==422; assert 'country' in r.text.lower()

def test_source_record_materialization_is_idempotent(client,write_headers):
    a=post_condition(client,write_headers,source_id='ocha-hdx-hapi',connector_id='ocha.hdx-hapi',source_record_id='stable-1')
    b=post_condition(client,write_headers,source_id='ocha-hdx-hapi',connector_id='ocha.hdx-hapi',source_record_id='stable-1')
    assert a['id']==b['id']

def add_live_observation(client, **overrides):
    data=dict(id='a'*64,connector_id='ocha.hdx-hapi',source_id='ocha-hdx-hapi',source_record_id='hapi-1',domain='humanitarian',metric='affected_people_idps',value_number=1250.0,value_text=None,unit='people',dimensions_json={'location_code':'PSE'},observed_at=NOW,published_at=NOW,retrieved_at=NOW,freshness_status='source_reported',quality_status='standardized_humanitarian_indicator',methodology_url='https://example.test/method',metadata_json={},public=True)
    data.update(overrides)
    with client.app.state.database.session_factory() as db:
        row=LiveDataObservation(**data); db.add(row); db.commit()
    return data['id']

def test_hdx_hapi_structured_observation_materializes(client,write_headers):
    oid=add_live_observation(client)
    r=client.post(f'/v1/humanitarian/materialize/live-observation/{oid}',headers=write_headers); assert r.status_code==200,r.text
    body=r.json(); assert body['materialized'] is True; assert body['reason']=='materialized'
    c=body['condition']; assert c['service_domain']=='displacement'; assert c['condition_kind']=='displacement'; assert c['value_number']==1250.0; assert c['country_code']=='PSE'

def test_reliefweb_report_metadata_is_not_promoted_to_operational_condition(client,write_headers):
    oid=add_live_observation(client,id='b'*64,connector_id='ocha.reliefweb-reports',source_id='ocha-reliefweb',source_record_id='rw-1',metric='report_metadata',value_number=None,value_text='Situation report')
    body=client.post(f'/v1/humanitarian/materialize/live-observation/{oid}',headers=write_headers).json()
    assert body['materialized'] is False; assert body['reason']=='report-metadata-not-operational-condition'

def test_unmapped_humanitarian_observation_requires_explicit_semantics(client,write_headers):
    oid=add_live_observation(client,id='c'*64,source_record_id='unknown-1',metric='unmapped_metric')
    body=client.post(f'/v1/humanitarian/materialize/live-observation/{oid}',headers=write_headers).json()
    assert body['materialized'] is False; assert body['reason']=='no-explicit-semantic-mapping'

def test_explicit_mapping_can_materialize_future_structured_connectors(client,write_headers):
    oid=add_live_observation(client,id='d'*64,source_record_id='mapped-1',metric='future_metric',value_number=None,value_text='limited',metadata_json={'humanitarian_mapping':{'service_domain':'water','condition_kind':'availability','semantic_role':'operational-condition'}},dimensions_json={'country_code':'PSE'})
    body=client.post(f'/v1/humanitarian/materialize/live-observation/{oid}',headers=write_headers).json()
    assert body['materialized'] is True; assert body['condition']['service_domain']=='water'; assert body['condition']['semantic_role']=='operational-condition'

def test_condition_creation_emits_stream_event(client,write_headers):
    post_condition(client,write_headers,source_record_id='event-1')
    s=client.get('/v1/reliability/stream?once=true'); assert s.status_code==200; assert 'humanitarian.condition.created' in s.text

def test_zero_records_means_unknown_not_normal(client):
    s=client.get('/v1/humanitarian/country/SDN/summary').json(); assert s['records']==0; assert s['zero_records_implication']=='unknown-not-normal'
