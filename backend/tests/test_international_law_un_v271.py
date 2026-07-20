from __future__ import annotations

import httpx

from app.connectors.adapters import ADAPTERS
from app.migrations import MIGRATIONS
from app.services.live_data import LiveDataRuntime


def test_v271_catalog_seeds_official_un_and_legal_sources(client):
    sources = client.get('/v1/live/sources')
    assert sources.status_code == 200
    payload = sources.json()
    source_ids = {item['id'] for item in payload}
    assert len(payload) == 40
    assert {
        'un-digital-library',
        'ohchr',
        'ocha-reliefweb',
        'ocha-hdx-hapi',
        'un-population',
        'un-comtrade',
        'unhcr',
        'un-treaty-collection',
        'icj',
        'un-ilc',
    } <= source_ids
    assert all(item['access_cost'] == 'free' for item in payload)
    assert all(item['credit_card_required'] is False for item in payload)

    connectors = client.get('/v1/live/connectors')
    assert connectors.status_code == 200
    connector_ids = {item['id'] for item in connectors.json()}
    assert len(connector_ids) == 39
    assert {
        'un.digital-library',
        'un.sdg-metadata',
        'ocha.reliefweb-reports',
        'ocha.hdx-hapi',
        'un.population-data',
        'un.comtrade',
        'unhcr.population',
        'ohchr.uhri-recommendations',
    } <= connector_ids


def test_v271_configuration_gates_and_adapter_registry(client):
    response = client.get('/v1/live/connectors/health')
    assert response.status_code == 200
    statuses = {item['id']: item['configuration_status'] for item in response.json()['connectors']}
    assert statuses['ocha.reliefweb-reports'] == 'registration_required'
    assert statuses['ohchr.uhri-recommendations'] == 'endpoint_registration_required'
    assert statuses['un.digital-library'] == 'configured'
    assert statuses['unhcr.population'] == 'configured'

    assert {
        'un_digital_library_search_v1',
        'un_sdg_metadata_v1',
        'reliefweb_reports_v2',
        'hdx_hapi_v2',
        'un_population_data_v1',
        'un_comtrade_public_v1',
        'unhcr_population_v1',
        'ohchr_uhri_v1',
    } <= set(ADAPTERS)
    assert any(version == '0008' for version, _description in MIGRATIONS)


def test_un_digital_library_ingestion_creates_legal_record_and_provenance(client, write_headers):
    payload = [
        {
            'recid': 987654,
            'title': {'title': 'Resolution 2728 (2024) / adopted by the Security Council'},
            'document_symbol': 'S/RES/2728 (2024)',
            'publication_date': '2024-03-25',
            'language': ['English', 'French'],
            'subjects': ['Ceasefire', 'Humanitarian assistance'],
            'corporate_author': 'United Nations Security Council',
            'urls': ['https://digitallibrary.un.org/record/987654'],
            'abstract': 'Official resolution metadata fixture.',
        }
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == '/search'
        assert request.url.params['of'] == 'recjson'
        assert request.url.params['p'] == 'S/RES/2728'
        return httpx.Response(200, json=payload)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    first = client.post(
        '/v1/live/connectors/un.digital-library/ingest',
        headers=write_headers,
        json={'parameters': {'query': 'S/RES/2728', 'limit': 10}, 'requested_by': 'pytest'},
    )
    assert first.status_code == 200, first.text
    assert first.json()['records_created'] == 1
    assert first.json()['details']['international_law_records_created'] == 1

    records = client.get('/v1/international-law/records?official_symbol=S%2FRES%2F2728%20%282024%29')
    assert records.status_code == 200, records.text
    assert records.json()['total'] == 1
    record = records.json()['items'][0]
    assert record['record_type'] == 'security_council_resolution'
    assert record['authority_level'] == 'official_security_council_resolution'
    assert record['legal_body'] == 'United Nations Security Council'
    assert record['languages'] == ['English', 'French']
    assert record['subjects'] == ['Ceasefire', 'Humanitarian assistance']
    assert record['canonical_source_url'] == 'https://digitallibrary.un.org/record/987654'
    assert len(record['content_hash']) == 64

    provenance = client.get(f"/v1/international-law/provenance/{record['id']}")
    assert provenance.status_code == 200, provenance.text
    body = provenance.json()
    assert body['source']['id'] == 'un-digital-library'
    assert body['connector']['id'] == 'un.digital-library'
    assert len(body['raw_record']['content_hash']) == 64
    assert 'Security Council' in body['authority_explanation']
    assert 'document symbol alone' in body['authority_explanation']

    stats = client.get('/v1/international-law/stats')
    assert stats.status_code == 200
    assert stats.json()['records'] == 1
    assert stats.json()['by_record_type']['security_council_resolution'] == 1

    second = client.post(
        '/v1/live/connectors/un.digital-library/ingest',
        headers=write_headers,
        json={'parameters': {'query': 'S/RES/2728', 'limit': 10}, 'requested_by': 'pytest'},
    )
    assert second.status_code == 200, second.text
    assert second.json()['records_created'] == 0
    assert second.json()['records_updated'] == 1
    assert second.json()['details']['international_law_records_created'] == 0
    assert second.json()['details']['international_law_records_updated'] == 1


def test_registration_gated_connectors_fail_closed(client, write_headers):
    reliefweb = client.post(
        '/v1/live/connectors/ocha.reliefweb-reports/ingest',
        headers=write_headers,
        json={'parameters': {'query': 'flood'}, 'requested_by': 'pytest'},
    )
    assert reliefweb.status_code == 503
    assert 'registration_required' in reliefweb.json()['detail']

    uhri = client.post(
        '/v1/live/connectors/ohchr.uhri-recommendations/ingest',
        headers=write_headers,
        json={'parameters': {'country': 'Kenya'}, 'requested_by': 'pytest'},
    )
    assert uhri.status_code == 503
    assert 'endpoint_registration_required' in uhri.json()['detail']


def test_authority_taxonomy_and_meta_advertise_v271(client):
    health = client.get('/health').json()
    assert health['version'] == '2.7.3'
    assert health['international_law_un_connector_pack'] is True

    taxonomy = client.get('/v1/international-law/authority-taxonomy')
    assert taxonomy.status_code == 200
    assert 'binding_treaty_obligation' in taxonomy.json()
    assert 'non_binding_recommendation' in taxonomy.json()
    assert 'statistical_observation' in taxonomy.json()

    meta = client.get('/v1/meta').json()
    assert 'international_law_record_store' in meta['capabilities']
    assert 'united_nations_connector_pack' in meta['capabilities']
    assert 'legal_authority_classification' in meta['capabilities']

    stats = client.get('/v1/stats').json()
    assert stats['live_data_sources'] == 40
    assert stats['live_data_connectors'] == 39
    assert stats['international_law_records'] == 0


def test_public_sdk_clients_expose_international_law_methods():
    from sc_platform_core_public.client import PublicApiClient
    assert callable(getattr(PublicApiClient, "international_law_records"))
    assert callable(getattr(PublicApiClient, "international_law_record"))
    assert callable(getattr(PublicApiClient, "international_law_authority_taxonomy"))


def test_scoped_public_authority_taxonomy(client, write_headers):
    application = client.post(
        "/v1/developer/applications",
        headers=write_headers,
        json={
            "name": "International Law Test Application",
            "owner_name": "Test Developer",
            "owner_email": "law-data@example.com",
            "organization": "Example Organization",
            "website_url": "https://example.com",
            "use_case": "Read public international-law authority classifications.",
            "status": "approved",
            "plan_id": "free",
            "metadata": {},
            "actor": "platform-administrator",
        },
    )
    assert application.status_code == 201, application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={
            "label": "International law data key",
            "scopes": ["data:read"],
            "created_by": "platform-administrator",
        },
    )
    assert issued.status_code == 201, issued.text
    key = issued.json()["api_key"]
    response = client.get(
        "/api/v1/international-law/authority-taxonomy",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["meta"]["api_version"] == "v1"
    assert "official_security_council_resolution" in response.json()["data"]
