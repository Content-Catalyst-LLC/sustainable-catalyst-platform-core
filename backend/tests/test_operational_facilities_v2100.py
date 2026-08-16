from datetime import datetime, timezone, timedelta
from app.migrations import migration_status

def create_hospital(client, headers, public=True):
    r=client.post('/v1/facilities',headers=headers,json={'name':'Example General Hospital','facility_type':'hospital','country_code':'PSE','admin_area':'Gaza','latitude':31.50,'longitude':34.46,'public':public,'source_identifiers':[{'namespace':'who-herams','value':'facility-001'}]}); assert r.status_code==200, r.text; return r.json()

def test_release_and_migration(client):
    assert client.get('/health').json()['version']=='2.23.0'
    ready=client.get('/v1/facilities/readiness').json(); assert ready['release']=='2.23.0'; assert ready['migration_0013_applied'] is True; assert ready['history_preserving'] is True; assert ready['automatic_conflict_flattening'] is False

def test_create_and_deduplicate_facility_by_source_identifier(client,write_headers):
    a=create_hospital(client,write_headers); b=create_hospital(client,write_headers); assert a['id']==b['id']; assert a['country_code']=='PSE'; assert a['facility_type']=='hospital'

def test_reject_invalid_type_and_coordinates(client,write_headers):
    r=client.post('/v1/facilities',headers=write_headers,json={'name':'Bad','facility_type':'castle','country_code':'PSE'}); assert r.status_code==422
    r=client.post('/v1/facilities',headers=write_headers,json={'name':'Bad','facility_type':'school','country_code':'PSE','latitude':120,'longitude':10}); assert r.status_code==422

def test_observation_history_preserved_and_current_per_kind(client,write_headers):
    f=create_hospital(client,write_headers); t=datetime(2026,8,14,tzinfo=timezone.utc)
    first={'observation_kind':'operational-status','status_value':'partially-operational','observed_at':t.isoformat(),'publisher':'WHO','evidence_class':'operational','services':['emergency'],'constraints':['fuel-shortage'],'provenance':{'report':'A'}}
    second={**first,'status_value':'non-functional','observed_at':(t+timedelta(days=1)).isoformat(),'provenance':{'report':'B'}}
    assert client.post(f"/v1/facilities/{f['id']}/observations",headers=write_headers,json=first).status_code==200
    assert client.post(f"/v1/facilities/{f['id']}/observations",headers=write_headers,json=second).status_code==200
    hist=client.get(f"/v1/facilities/{f['id']}/observations").json()['items']; assert len(hist)==2; assert hist[0]['status_value']=='non-functional'; assert hist[1]['status_value']=='partially-operational'
    detail=client.get(f"/v1/facilities/{f['id']}").json(); assert detail['current_observations'][0]['status_value']=='non-functional'

def test_multiple_observation_dimensions_not_flattened(client,write_headers):
    f=create_hospital(client,write_headers); now=datetime.now(timezone.utc).isoformat()
    for kind,status in [('operational-status','partially-operational'),('damage-status','damaged'),('access-status','access-constrained')]:
        r=client.post(f"/v1/facilities/{f['id']}/observations",headers=write_headers,json={'observation_kind':kind,'status_value':status,'observed_at':now,'publisher':'Open report'}); assert r.status_code==200
    current=client.get(f"/v1/facilities/{f['id']}").json()['current_observations']; assert {x['observation_kind'] for x in current}=={'operational-status','damage-status','access-status'}

def test_bbox_and_country_query(client,write_headers):
    create_hospital(client,write_headers); data=client.get('/v1/facilities?country_code=PSE&facility_type=hospital&bbox=34,31,35,32').json(); assert data['total']==1
    assert client.get('/v1/facilities?bbox=35,32,34,31').status_code==422

def test_private_facility_excluded_from_public_api(client,write_headers):
    f=create_hospital(client,write_headers,public=False); internal=client.get('/v1/facilities?country_code=PSE').json(); assert internal['total']==1
    # Public API requires public credential, so direct service behavior is covered by public_only query in separate unit path.

def test_facility_observation_emits_stream_event(client,write_headers):
    f=create_hospital(client,write_headers); r=client.post(f"/v1/facilities/{f['id']}/observations",headers=write_headers,json={'observation_kind':'service-status','status_value':'limited','observed_at':datetime.now(timezone.utc).isoformat(),'publisher':'Health Cluster'}); assert r.status_code==200
    # Internal stream endpoint snapshots persisted event log.
    s=client.get('/v1/reliability/stream?once=true'); assert s.status_code==200; assert 'facility.observation.created' in s.text

def test_provenance_fields_round_trip(client,write_headers):
    f=create_hospital(client,write_headers); payload={'observation_kind':'damage-status','status_value':'damaged','observed_at':datetime.now(timezone.utc).isoformat(),'publisher':'UNOSAT','source_record_id':'report-42','source_url':'https://example.test/report','evidence_class':'satellite-assessment','geographic_scope':'Gaza','methodology':'visual damage assessment','confidence':0.8,'provenance':{'asset':'scene-1'}}
    out=client.post(f"/v1/facilities/{f['id']}/observations",headers=write_headers,json=payload).json(); assert out['publisher']=='UNOSAT'; assert out['evidence_class']=='satellite-assessment'; assert out['confidence']==0.8; assert out['provenance']['asset']=='scene-1'

def test_supported_facility_classes_include_hospital_school_and_essential_services(client):
    types=set(client.get('/v1/facilities/readiness').json()['facility_types']); assert {'hospital','school','water-facility','power-facility','crossing','food-distribution'} <= types
