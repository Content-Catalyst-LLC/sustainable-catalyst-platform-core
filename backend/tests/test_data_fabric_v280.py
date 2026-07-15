from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import httpx

from app.migrations import MIGRATIONS
from app.models import ScientificDataRecord
from app.services.live_data import LiveDataRuntime


def _public_key(client, write_headers):
    application = client.post('/v1/developer/applications', headers=write_headers, json={
        'name': 'Data Fabric Test', 'owner_name': 'Tester', 'owner_email': 'fabric@example.com',
        'organization': 'Test', 'website_url': 'https://example.com',
        'use_case': 'Read public geospatial, time-series, asset, and STAC records.',
        'status': 'approved', 'plan_id': 'free', 'metadata': {}, 'actor': 'admin',
    })
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={'label': 'Fabric', 'scopes': ['data:read'], 'created_by': 'admin'},
    )
    return issued.json()['api_key']


def test_v280_migration_health_meta_and_empty_stats(client):
    assert any(version == '0011' for version, _ in MIGRATIONS)
    health = client.get('/health').json()
    assert health['version'] == '2.8.0'
    assert health['geospatial_time_series_scientific_data_fabric'] is True
    assert health['stac_catalog'] is True
    meta = client.get('/v1/meta').json()
    for capability in {
        'geospatial_data_fabric', 'portable_geojson_store', 'time_series_registry',
        'scientific_asset_registry', 'stac_1_0_catalog', 'map_layer_registry',
    }:
        assert capability in meta['capabilities']
    stats = client.get('/v1/fabric/stats').json()
    assert stats['geospatial_features'] == 0
    assert stats['time_series'] == 0
    assert stats['stac_collections'] == 0
    assert stats['database_dialect'] == 'sqlite'
    assert stats['postgis_mode'] == 'portable_geojson'
    capabilities = client.get('/v1/fabric/capabilities').json()
    assert capabilities['stac_version'] == '1.0.0'
    assert {'fits', 'netcdf', 'zarr', 'geoparquet', 'cog', 'pmtiles', 'sdmx', 'tap_adql'} <= set(capabilities['formats'])


def test_ingestion_materializes_timeseries_geojson_assets_and_stac(client, write_headers):
    payload = {'status': 'COMPLETE', 'data': [{
        'obsid': '12345', 'obs_id': 'jw01234001001_02101_00001_nrca1',
        'obs_collection': 'JWST', 'instrument_name': 'NIRCAM/IMAGE',
        'target_name': 'NGC 3324', 's_ra': 159.2, 's_dec': -58.6,
        't_min': 59770.0, 'dataproduct_type': 'image', 'proposal_id': '1234',
        'dataRights': 'PUBLIC', 'dataURL': 'https://example.test/jwst-observation.fits',
        'dataProductType': 'FITS',
    }]}

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == 'POST'
        return httpx.Response(200, json=payload)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    response = client.post(
        '/v1/live/connectors/mast.observations/ingest',
        headers=write_headers,
        json={'parameters': {'collection': 'JWST', 'target_name': 'NGC 3324'}, 'requested_by': 'pytest'},
    )
    assert response.status_code == 200, response.text
    details = response.json()['details']
    assert details['fabric_time_series_created'] == 1
    assert details['fabric_time_series_points_created'] == 1
    assert details['fabric_geospatial_features_created'] >= 1
    assert details['fabric_scientific_assets_created'] == 1
    assert details['fabric_stac_collections_created'] == 1
    assert details['fabric_stac_items_created'] == 1

    series = client.get('/v1/fabric/timeseries?metric=telescope_observation').json()
    assert series['total'] == 1
    series_id = series['items'][0]['id']
    points = client.get(f'/v1/fabric/timeseries/{series_id}/points').json()
    assert points['total'] == 1
    assert points['items'][0]['partition_key'] == '2022-07'

    feature_json = client.get('/v1/fabric/features.geojson?bbox=159,-59,160,-58')
    assert feature_json.status_code == 200
    assert feature_json.headers['content-type'].startswith('application/geo+json')
    collection = feature_json.json()
    assert collection['type'] == 'FeatureCollection'
    assert collection['numberMatched'] >= 1
    assert collection['features'][0]['geometry']['type'] == 'Point'

    assets = client.get('/v1/fabric/assets?source_id=mast').json()
    assert assets['total'] == 1
    assert assets['items'][0]['format'] == 'fits'
    assert assets['items'][0]['storage_mode'] == 'remote'

    stac = client.get('/v1/stac/collections').json()
    assert stac['numberMatched'] == 1
    collection_id = stac['collections'][0]['id']
    items = client.get(f'/v1/stac/collections/{collection_id}/items').json()
    assert items['numberMatched'] == 1
    assert items['features'][0]['assets']['data']['sc:format'] == 'fits'

    registry_stats = client.get('/v1/stats').json()
    assert registry_stats['time_series_definitions'] == 1
    assert registry_stats['time_series_points'] == 1
    assert registry_stats['scientific_data_assets'] == 1
    assert registry_stats['stac_items'] == 1


def test_backfill_is_idempotent_and_registers_cog_map_layer(client, write_headers):
    now = datetime(2026, 7, 14, tzinfo=timezone.utc)
    with client.app.state.database.session_factory() as db:
        record = ScientificDataRecord(
            id='cog-record', connector_id='nasa.cmr-collections', source_id='nasa-earthdata',
            raw_record_id=None, source_record_id='cog-source-record', record_type='earth_science_dataset',
            discipline='earth_science', title='Test COG layer', summary='A test cloud optimized raster.',
            dataset_id='TEST-COG', collection='Test Earth Observation', mission='Test Mission', instrument='Test Sensor',
            target='Earth', doi=None, access_url='https://example.test/layer.tif', landing_page_url='https://example.test/layer',
            geometry_json={'type': 'Polygon', 'coordinates': [[[-88, 41], [-87, 41], [-87, 42], [-88, 42], [-88, 41]]]},
            observation_start=now, observation_end=now, published_at=now,
            identifiers_json={'dataset': 'TEST-COG'}, keywords_json=['earth observation'], variables_json=['reflectance'],
            file_formats_json=['COG'], quality_status='test', license_name='CC BY 4.0', attribution='Test Provider',
            content_hash=hashlib.sha256(b'test-cog').hexdigest(), metadata_json={}, public=True,
        )
        db.add(record)
        db.commit()

    first = client.post('/v1/fabric/materialize', headers=write_headers)
    assert first.status_code == 200, first.text
    assert first.json()['map_layers_created'] == 1
    second = client.post('/v1/fabric/materialize', headers=write_headers)
    assert second.status_code == 200
    assert second.json()['map_layers_created'] == 0
    layers = client.get('/v1/fabric/map-layers?layer_type=cog').json()
    assert layers['total'] == 1
    assert layers['items'][0]['endpoint_url'] == 'https://example.test/layer.tif'
    assert layers['items'][0]['bounds'] == [-88.0, 41.0, -87.0, 42.0]


def test_public_data_fabric_and_stac_routes(client, write_headers):
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    assert client.get('/api/v1/fabric/capabilities', headers=headers).status_code == 200
    response = client.get('/api/v1/fabric/timeseries', headers=headers)
    assert response.status_code == 200
    assert response.json()['meta']['api_version'] == 'v1'
    assert client.get('/api/v1/fabric/features.geojson', headers=headers).status_code == 200
    stac = client.get('/api/v1/stac', headers=headers)
    assert stac.status_code == 200
    assert stac.json()['stac_version'] == '1.0.0'


def test_public_sdk_data_fabric_methods(monkeypatch):
    from sc_platform_core_public.client import PublicApiClient

    calls = []

    class Response:
        is_error = False
        def json(self): return {'data': []}

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr(httpx, 'request', fake_request)
    sdk = PublicApiClient('https://core.example', 'test-key')
    sdk.fabric_capabilities()
    sdk.geospatial_features(bbox='-88,41,-87,42')
    sdk.time_series(metric='temperature')
    sdk.time_series_points('series-id')
    sdk.scientific_assets(format='fits')
    sdk.map_layers(layer_type='cog')
    assert calls[0][1].endswith('/api/v1/fabric/capabilities')
    assert calls[1][2]['params'] == {'bbox': '-88,41,-87,42'}
    assert calls[3][1].endswith('/api/v1/fabric/timeseries/series-id/points')
    assert calls[5][2]['params'] == {'layer_type': 'cog'}
