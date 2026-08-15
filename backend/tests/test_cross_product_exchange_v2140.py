from datetime import datetime, timezone


def make_facility(client, headers, public=True):
    r = client.post('/v1/facilities', headers=headers, json={
        'name':'Exchange Hospital','facility_type':'hospital','country_code':'PSE',
        'latitude':31.5,'longitude':34.46,'public':public,
        'source_identifiers':[{'namespace':'test','value':'exchange-hospital'}],
    })
    assert r.status_code == 200, r.text
    return r.json()


def make_package(client, headers, facility_id, **overrides):
    payload = {
        'origin_product':'site-intelligence',
        'target_product':'workspace',
        'title':'Palestine facility evidence handoff',
        'purpose':'Research notebook evidence handoff',
        'visibility':'internal',
        'idempotency_key':'exchange-case-1',
        'items':[{'artifact_type':'facility','subject_type':'facility','subject_id':facility_id,'snapshot_mode':'reference+snapshot','provenance':{'workflow':'country-intelligence'}}],
        'provenance':{'requested_by':'integration-test'},
    }
    payload.update(overrides)
    return client.post('/v1/exchange/packages', headers=headers, json=payload)


def test_release_readiness_and_migration(client):
    assert client.get('/health').json()['version'] == '2.18.0'
    ready = client.get('/v1/exchange/readiness').json()
    assert ready['release'] == '2.18.0'
    assert ready['migration_0017_applied'] is True
    assert ready['reference_first'] is True
    assert ready['non_destructive'] is True
    assert ready['automatic_truth_promotion'] is False
    assert ready['automatic_cross_product_delivery'] is False


def test_create_reference_first_package_with_governed_snapshot(client, write_headers):
    f = make_facility(client, write_headers)
    r = make_package(client, write_headers, f['id'])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['origin_product'] == 'site-intelligence'
    assert body['target_product'] == 'workspace'
    assert body['delivery_mode'] == 'pull'
    assert body['governance']['source_artifacts_retained'] is True
    item = body['items'][0]
    assert item['canonical_uri'].endswith(f['id'])
    assert item['snapshot']['id'] == f['id']
    assert item['truth_precedence'] == 'inherit-from-subject'
    assert item['transformation_state'] == 'unaltered-reference'


def test_idempotency_does_not_duplicate_package(client, write_headers):
    f = make_facility(client, write_headers)
    a = make_package(client, write_headers, f['id']).json()
    b = make_package(client, write_headers, f['id']).json()
    assert a['id'] == b['id']
    rows = client.get('/v1/exchange/packages?origin_product=site-intelligence').json()['items']
    assert len(rows) == 1


def test_unknown_subject_and_unknown_product_are_rejected(client, write_headers):
    r = client.post('/v1/exchange/packages', headers=write_headers, json={
        'origin_product':'unknown-product','target_product':'workspace','title':'Bad',
        'items':[{'subject_type':'facility','subject_id':'nope'}],
    })
    assert r.status_code == 422
    r = client.post('/v1/exchange/packages', headers=write_headers, json={
        'origin_product':'site-intelligence','target_product':'workspace','title':'Bad',
        'items':[{'subject_type':'facility','subject_id':'nope'}],
    })
    assert r.status_code == 422


def test_public_package_cannot_include_private_source(client, write_headers):
    f = make_facility(client, write_headers, public=False)
    r = make_package(client, write_headers, f['id'], visibility='public', idempotency_key='private-public')
    assert r.status_code == 422
    assert 'non-public' in r.text


def test_sensitive_snapshot_metadata_is_rejected(client, write_headers):
    f = make_facility(client, write_headers)
    r = make_package(client, write_headers, f['id'], idempotency_key='secret-case', provenance={'api_token':'do-not-store'})
    assert r.status_code == 422
    assert 'Sensitive field' in r.text


def test_receipt_must_match_target_and_preserves_source(client, write_headers):
    f = make_facility(client, write_headers)
    p = make_package(client, write_headers, f['id']).json()
    wrong = client.post(f"/v1/exchange/packages/{p['id']}/receipts", headers=write_headers, json={'target_product':'lab','state':'accepted'})
    assert wrong.status_code == 422
    ok = client.post(f"/v1/exchange/packages/{p['id']}/receipts", headers=write_headers, json={'target_product':'workspace','state':'derived','derived_object_id':'notebook-123'})
    assert ok.status_code == 200
    detail = client.get(f"/v1/exchange/packages/{p['id']}").json()
    assert detail['state'] == 'derived'
    assert detail['items'][0]['subject_id'] == f['id']
    assert client.get(f"/v1/facilities/{f['id']}").status_code == 200


def test_package_and_receipt_emit_private_stream_events(client, write_headers):
    f = make_facility(client, write_headers)
    p = make_package(client, write_headers, f['id']).json()
    client.post(f"/v1/exchange/packages/{p['id']}/receipts", headers=write_headers, json={'target_product':'workspace','state':'acknowledged'})
    from app.services.reliability import list_stream_events
    with client.app.state.database.session_factory() as db:
        event_types = [event.event_type for event in list_stream_events(db, public_only=False, limit=100)]
    assert 'exchange.package.created' in event_types
    assert 'exchange.package.receipt' in event_types


def test_multiple_evidence_families_can_share_one_package_without_blending(client, write_headers):
    f = make_facility(client, write_headers)
    obs = client.post(f"/v1/facilities/{f['id']}/observations", headers=write_headers, json={
        'observation_kind':'operational-status','status_value':'partially-operational',
        'observed_at':datetime.now(timezone.utc).isoformat(),'publisher':'WHO'
    }).json()
    r = client.post('/v1/exchange/packages', headers=write_headers, json={
        'origin_product':'site-intelligence','target_product':'decision-studio','title':'Evidence packet',
        'idempotency_key':'multi-family','items':[
            {'artifact_type':'facility','subject_type':'facility','subject_id':f['id']},
            {'artifact_type':'observation','subject_type':'facility-observation','subject_id':obs['id']},
        ]
    })
    assert r.status_code == 200, r.text
    items = r.json()['items']
    assert len(items) == 2
    assert {x['subject_type'] for x in items} == {'facility','facility-observation'}
    assert all(x['truth_precedence'] == 'inherit-from-subject' for x in items)


def test_exchange_data_is_not_exposed_by_public_readiness(client):
    ready = client.get('/v1/exchange/readiness').json()
    assert ready['private_package_public_api_exposure'] is False
    assert 'workspace' in ready['products']
    assert 'knowledge-library' in ready['products']
    assert 'lab' in ready['products']
