from __future__ import annotations

import httpx

from app.connectors.adapters import ADAPTERS
from app.migrations import MIGRATIONS
from app.services.live_data import LiveDataRuntime


def _public_key(client, write_headers):
    application = client.post('/v1/developer/applications', headers=write_headers, json={
        'name':'Scientific Data Test Application','owner_name':'Test Developer','owner_email':'science@example.com',
        'organization':'Example Organization','website_url':'https://example.com','use_case':'Read public scientific dataset records.',
        'status':'approved','plan_id':'free','metadata':{},'actor':'platform-administrator'})
    assert application.status_code == 201, application.text
    issued = client.post(f"/v1/developer/applications/{application.json()['id']}/credentials", headers=write_headers,
        json={'label':'Science key','scopes':['data:read'],'created_by':'platform-administrator'})
    assert issued.status_code == 201, issued.text
    return issued.json()['api_key']


def test_v272_catalog_and_adapters(client):
    sources = client.get('/v1/live/sources').json()
    connectors = client.get('/v1/live/connectors').json()
    source_ids = {item['id'] for item in sources}
    connector_ids = {item['id'] for item in connectors}
    assert len(sources) == 40
    assert len(connectors) == 39
    assert {'noaa-ncei','ecmwf','usgs-water','ncbi','pubchem','gbif','materials-project','mast','heasarc','irsa','eso','nasa-open-apis'} <= source_ids
    assert {'nasa.cmr-collections','nasa.apod','noaa.ncei-data','ecmwf.open-data-index','usgs.water-instantaneous','ncbi.entrez-search','pubchem.compound-properties','gbif.occurrences','materials-project.summary','mast.observations','heasarc.xamin','irsa.tap','eso.tap'} <= connector_ids
    assert {'nasa_cmr_collections_v1','nasa_apod_v1','noaa_ncei_data_v1','ecmwf_open_data_index_v1','usgs_water_iv_v1','ncbi_entrez_search_v1','pubchem_compound_properties_v1','gbif_occurrence_search_v1','materials_project_summary_v1','mast_observations_v1','heasarc_xamin_v1','ivoa_tap_json_v1'} <= set(ADAPTERS)
    assert any(version == '0009' for version, _ in MIGRATIONS)


def test_nasa_cmr_ingestion_creates_scientific_record_and_provenance(client, write_headers):
    payload={'feed':{'entry':[{
        'id':'C123456-NASA','dataset_id':'MODIS Land Surface Temperature','short_name':'MOD11A1','version_id':'061',
        'summary':'Daily global land surface temperature and emissivity.','time_start':'2000-02-24T00:00:00Z',
        'updated':'2026-07-01T12:00:00Z','doi':'10.5067/MODIS/MOD11A1.061','data_center':'LP DAAC',
        'boxes':['-90 -180 90 180'],'links':[{'href':'https://example.test/MOD11A1','rel':'http://esipfed.org/ns/fedsearch/1.1/data#'}]
    }]}}
    async def handler(request:httpx.Request)->httpx.Response:
        assert request.url.path == '/search/collections.json'
        assert request.url.params['keyword'] == 'land surface temperature'
        return httpx.Response(200,json=payload)
    client.app.state.live_data_runtime=LiveDataRuntime(client.app.state.settings,transport=httpx.MockTransport(handler))
    first=client.post('/v1/live/connectors/nasa.cmr-collections/ingest',headers=write_headers,json={'parameters':{'keyword':'land surface temperature'},'requested_by':'pytest'})
    assert first.status_code == 200, first.text
    assert first.json()['details']['scientific_data_records_created'] == 1
    records=client.get('/v1/science/records?dataset_id=MOD11A1')
    assert records.status_code == 200
    assert records.json()['total'] == 1
    record=records.json()['items'][0]
    assert record['record_type'] == 'earth_science_dataset'
    assert record['discipline'] == 'earth_science'
    assert record['doi'] == '10.5067/MODIS/MOD11A1.061'
    provenance=client.get(f"/v1/science/provenance/{record['id']}")
    assert provenance.status_code == 200
    assert provenance.json()['source']['id'] == 'nasa-earthdata'
    assert provenance.json()['connector']['id'] == 'nasa.cmr-collections'
    second=client.post('/v1/live/connectors/nasa.cmr-collections/ingest',headers=write_headers,json={'parameters':{'keyword':'land surface temperature'},'requested_by':'pytest'})
    assert second.status_code == 200
    assert second.json()['details']['scientific_data_records_updated'] == 1


def test_pubchem_compound_normalization(client, write_headers):
    payload={'PropertyTable':{'Properties':[{'CID':962,'Title':'Water','MolecularFormula':'H2O','MolecularWeight':'18.015','CanonicalSMILES':'O','InChI':'InChI=1S/H2O/h1H2','InChIKey':'XLYOFNOQVPJJNP-UHFFFAOYSA-N','IUPACName':'oxidane','ExactMass':'18.010565'}]}}
    async def handler(request:httpx.Request)->httpx.Response:
        assert '/name/water/property/' in request.url.path
        return httpx.Response(200,json=payload)
    client.app.state.live_data_runtime=LiveDataRuntime(client.app.state.settings,transport=httpx.MockTransport(handler))
    response=client.post('/v1/live/connectors/pubchem.compound-properties/ingest',headers=write_headers,json={'parameters':{'namespace':'name','identifier':'water'},'requested_by':'pytest'})
    assert response.status_code == 200, response.text
    science=client.get('/v1/science/records?record_type=chemical_compound').json()
    assert science['total'] == 1
    assert science['items'][0]['identifiers']['cid'] == '962'
    live=client.get('/v1/live/observations/latest?connector_id=pubchem.compound-properties').json()
    assert live['items'][0]['value_number'] == 18.015


def test_mast_post_request_and_telescope_record(client, write_headers):
    payload={'status':'COMPLETE','data':[{'obsid':'12345','obs_id':'jw01234001001_02101_00001_nrca1','obs_collection':'JWST','instrument_name':'NIRCAM/IMAGE','target_name':'NGC 3324','s_ra':159.2,'s_dec':-58.6,'t_min':59770.0,'dataproduct_type':'image','proposal_id':'1234','dataRights':'PUBLIC'}]}
    async def handler(request:httpx.Request)->httpx.Response:
        assert request.method == 'POST'
        body=(await request.aread()).decode()
        assert 'Mast.Caom.Filtered' in body
        return httpx.Response(200,json=payload)
    client.app.state.live_data_runtime=LiveDataRuntime(client.app.state.settings,transport=httpx.MockTransport(handler))
    response=client.post('/v1/live/connectors/mast.observations/ingest',headers=write_headers,json={'parameters':{'collection':'JWST','target_name':'NGC 3324'},'requested_by':'pytest'})
    assert response.status_code == 200, response.text
    records=client.get('/v1/science/records?mission=JWST').json()
    assert records['total'] == 1
    assert records['items'][0]['instrument'] == 'NIRCAM/IMAGE'
    assert records['items'][0]['target'] == 'NGC 3324'


def test_registration_gate_and_read_only_adql(client, write_headers):
    health=client.get('/v1/live/connectors/health').json()
    statuses={item['id']:item['configuration_status'] for item in health['connectors']}
    assert statuses['materials-project.summary'] == 'credential_required'
    blocked=client.post('/v1/live/connectors/materials-project.summary/ingest',headers=write_headers,json={'parameters':{'formula':'SiO2'},'requested_by':'pytest'})
    assert blocked.status_code == 503
    unsafe=client.post('/v1/live/connectors/irsa.tap/ingest',headers=write_headers,json={'parameters':{'query':'DELETE FROM ivoa.obscore'},'requested_by':'pytest'})
    assert unsafe.status_code == 422
    assert 'SELECT' in unsafe.json()['detail'] or 'prohibited' in unsafe.json()['detail']


def test_health_meta_stats_and_public_science_api(client, write_headers):
    health=client.get('/health').json()
    assert health['version'] == '2.7.3'
    assert health['scientific_data_connector_pack'] is True
    meta=client.get('/v1/meta').json()
    assert 'scientific_data_record_store' in meta['capabilities']
    assert 'read_only_adql_gateway' in meta['capabilities']
    stats=client.get('/v1/stats').json()
    assert stats['live_data_sources'] == 40
    assert stats['live_data_connectors'] == 39
    assert stats['scientific_data_records'] == 0
    types=client.get('/v1/science/record-types')
    assert types.status_code == 200
    assert 'telescope_observation' in types.json()
    key=_public_key(client,write_headers)
    public=client.get('/api/v1/science/record-types',headers={'Authorization':f'Bearer {key}'})
    assert public.status_code == 200
    assert public.json()['meta']['api_version'] == 'v1'


def test_public_sdk_exposes_scientific_methods():
    from sc_platform_core_public.client import PublicApiClient
    assert callable(getattr(PublicApiClient,'scientific_records'))
    assert callable(getattr(PublicApiClient,'scientific_record'))
    assert callable(getattr(PublicApiClient,'scientific_record_types'))


def test_apod_noaa_and_ecmwf_adapters(client, write_headers):
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith('/planetary/apod'):
            return httpx.Response(200, json={
                'date': '2026-07-14',
                'title': 'A Test Nebula',
                'explanation': 'Official public astronomy media metadata.',
                'media_type': 'image',
                'url': 'https://example.test/nebula.jpg',
                'hdurl': 'https://example.test/nebula-hd.jpg',
                'service_version': 'v1',
            })
        if path.endswith('/access/services/data/v1'):
            return httpx.Response(200, json=[{
                'DATE': '2026-07-14T12:00:00Z',
                'STATION': 'TEST0001',
                'NAME': 'Test Climate Station',
                'LATITUDE': '41.88',
                'LONGITUDE': '-87.63',
                'TAVG': '25.1',
            }])
        if path.endswith('.index'):
            return httpx.Response(200, text='{"param":"2t","levelist":"sfc","_offset":0,"_length":2048}\n')
        raise AssertionError(path)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    apod = client.post(
        '/v1/live/connectors/nasa.apod/ingest',
        headers=write_headers,
        json={'parameters': {'date': '2026-07-14'}, 'requested_by': 'pytest'},
    )
    assert apod.status_code == 200, apod.text
    noaa = client.post(
        '/v1/live/connectors/noaa.ncei-data/ingest',
        headers=write_headers,
        json={'parameters': {'dataset': 'daily-summaries', 'start_date': '2026-07-14', 'end_date': '2026-07-14'}, 'requested_by': 'pytest'},
    )
    assert noaa.status_code == 200, noaa.text
    ecmwf = client.post(
        '/v1/live/connectors/ecmwf.open-data-index/ingest',
        headers=write_headers,
        json={'parameters': {'date': '20260714', 'run': '00', 'stream': 'oper', 'type': 'fc', 'step': 6}, 'requested_by': 'pytest'},
    )
    assert ecmwf.status_code == 200, ecmwf.text

    records = client.get('/v1/science/records?limit=20').json()['items']
    types = {item['record_type'] for item in records}
    assert {'astronomy_image', 'environmental_observation', 'forecast_field'} <= types


def test_usgs_water_ncbi_and_gbif_adapters(client, write_headers):
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith('/nwis/iv/'):
            return httpx.Response(200, json={'value': {'timeSeries': [{
                'sourceInfo': {
                    'siteName': 'Chicago River at Test Site',
                    'siteCode': [{'value': '05536123'}],
                    'geoLocation': {'geogLocation': {'latitude': 41.9, 'longitude': -87.65}},
                },
                'variable': {
                    'variableCode': [{'value': '00060'}],
                    'variableDescription': 'Discharge, cubic feet per second',
                    'unit': {'unitCode': 'ft3/s'},
                },
                'values': [{'value': [{'value': '125.4', 'dateTime': '2026-07-14T12:00:00Z', 'qualifiers': ['P']}]}],
            }]}})
        if path.endswith('/esearch.fcgi'):
            return httpx.Response(200, json={'esearchresult': {'count': '1', 'idlist': ['12345678'], 'querytranslation': 'climate[All Fields]'}})
        if path.endswith('/occurrence/search'):
            return httpx.Response(200, json={'count': 1, 'results': [{
                'key': 987654321,
                'scientificName': 'Danaus plexippus',
                'eventDate': '2026-07-10T00:00:00Z',
                'decimalLatitude': 41.88,
                'decimalLongitude': -87.63,
                'countryCode': 'US',
                'basisOfRecord': 'HUMAN_OBSERVATION',
                'datasetKey': 'dataset-1',
                'datasetTitle': 'Test Biodiversity Dataset',
                'license': 'CC_BY_4_0',
            }]})
        raise AssertionError(path)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    water = client.post(
        '/v1/live/connectors/usgs.water-instantaneous/ingest',
        headers=write_headers,
        json={'parameters': {'sites': '05536123', 'parameter_cd': '00060'}, 'requested_by': 'pytest'},
    )
    assert water.status_code == 200, water.text
    ncbi = client.post(
        '/v1/live/connectors/ncbi.entrez-search/ingest',
        headers=write_headers,
        json={'parameters': {'db': 'pubmed', 'term': 'climate'}, 'requested_by': 'pytest'},
    )
    assert ncbi.status_code == 200, ncbi.text
    gbif = client.post(
        '/v1/live/connectors/gbif.occurrences/ingest',
        headers=write_headers,
        json={'parameters': {'scientific_name': 'Danaus plexippus', 'country': 'US'}, 'requested_by': 'pytest'},
    )
    assert gbif.status_code == 200, gbif.text

    stats = client.get('/v1/science/stats').json()
    assert stats['by_record_type']['water_observation'] == 1
    assert stats['by_record_type']['biomedical_database_record'] == 1
    assert stats['by_record_type']['biodiversity_occurrence'] == 1


def test_heasarc_irsa_and_eso_archive_adapters(client, write_headers):
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith('/xamin/query'):
            return httpx.Response(200, json={'rows': [{
                'id': 'heasarc-1',
                'name': 'High Energy Source',
                'ra': 10.5,
                'dec': -20.2,
                'mission': 'TESTSAT',
                'instrument': 'XRT',
            }]})
        if path.endswith('/TAP/sync'):
            return httpx.Response(200, json={
                'metadata': [{'name': 'source_id'}, {'name': 'main_id'}, {'name': 'ra'}, {'name': 'dec'}],
                'data': [['irsa-1', 'Infrared Source', 12.3, -4.5]],
            })
        if path.endswith('/tap_obs/sync'):
            return httpx.Response(200, json={
                'metadata': [{'name': 'obs_publisher_did'}, {'name': 'obs_id'}, {'name': 'target_name'}, {'name': 's_ra'}, {'name': 's_dec'}, {'name': 'obs_collection'}],
                'data': [['ivo://eso/obs-1', 'eso-obs-1', 'NGC 1234', 42.0, -11.0, 'ESO']],
            })
        raise AssertionError(path)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    heasarc = client.post(
        '/v1/live/connectors/heasarc.xamin/ingest',
        headers=write_headers,
        json={'parameters': {'table': 'heasarc_test'}, 'requested_by': 'pytest'},
    )
    assert heasarc.status_code == 200, heasarc.text
    irsa = client.post(
        '/v1/live/connectors/irsa.tap/ingest',
        headers=write_headers,
        json={'parameters': {'query': 'SELECT TOP 10 * FROM test_table'}, 'requested_by': 'pytest'},
    )
    assert irsa.status_code == 200, irsa.text
    eso = client.post(
        '/v1/live/connectors/eso.tap/ingest',
        headers=write_headers,
        json={'parameters': {'query': 'SELECT TOP 10 * FROM ivoa.obscore'}, 'requested_by': 'pytest'},
    )
    assert eso.status_code == 200, eso.text

    records = client.get('/v1/science/records?discipline=astronomy&limit=20').json()
    assert records['total'] == 2
    high_energy = client.get('/v1/science/records?discipline=high_energy_astrophysics').json()
    assert high_energy['total'] == 1


def test_materials_project_adapter_with_free_key(client, write_headers):
    from dataclasses import replace

    settings = replace(client.app.state.settings, materials_project_api_key='test-free-registration-key')

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers['X-API-KEY'] == 'test-free-registration-key'
        return httpx.Response(200, json={
            'data': [{
                'material_id': 'mp-149',
                'formula_pretty': 'Si',
                'chemsys': 'Si',
                'formation_energy_per_atom': -0.01,
                'band_gap': 0.6,
                'is_stable': True,
                'is_metal': False,
                'last_updated': '2026-07-01T00:00:00Z',
            }],
            'meta': {'db_version': '2026.07.01'},
        })

    client.app.state.live_data_runtime = LiveDataRuntime(
        settings,
        transport=httpx.MockTransport(handler),
    )
    response = client.post(
        '/v1/live/connectors/materials-project.summary/ingest',
        headers=write_headers,
        json={'parameters': {'formula': 'Si'}, 'requested_by': 'pytest'},
    )
    assert response.status_code == 200, response.text
    record = client.get('/v1/science/records?record_type=material').json()['items'][0]
    assert record['dataset_id'] == 'mp-149'
    assert record['metadata']['database_version'] == '2026.07.01'
