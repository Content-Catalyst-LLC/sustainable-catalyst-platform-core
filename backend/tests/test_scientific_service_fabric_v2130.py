from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app.models import MapLayer, ScientificDataAsset, ScientificDataRecord, ScientificDomainBinding, TimeSeriesDefinition
from app.migrations import MIGRATIONS

NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def add_record(client, *, rid: str, source_id: str, connector_id: str, discipline: str, title: str, mission: str | None = None, target: str | None = None, keywords=None, variables=None, metadata=None, access_url: str | None = None):
    with client.app.state.database.session_factory() as db:
        row=ScientificDataRecord(
            id=rid, connector_id=connector_id, source_id=source_id, raw_record_id=None, source_record_id=f"source-{rid}",
            record_type="environmental_observation" if discipline != "astronomy" else "telescope_observation",
            discipline=discipline, title=title, summary=title, dataset_id=f"dataset-{rid}", collection=f"collection-{rid}", mission=mission,
            instrument=None, target=target, doi=None, access_url=access_url, landing_page_url=None, geometry_json=None,
            observation_start=NOW, observation_end=NOW, published_at=NOW, identifiers_json={}, keywords_json=keywords or [],
            variables_json=variables or [], file_formats_json=["FITS"] if discipline == "astronomy" else ["NetCDF"], quality_status="source_reported",
            license_name="public", attribution=source_id, content_hash=hashlib.sha256(rid.encode()).hexdigest(), metadata_json=metadata or {}, public=True,
        )
        db.add(row); db.commit()
    return rid


def public_key(client, write_headers):
    app=client.post('/v1/developer/applications',headers=write_headers,json={
        'name':'Scientific Fabric Test','owner_name':'Tester','owner_email':'science-fabric@example.com','organization':'Test',
        'website_url':'https://example.com','use_case':'Read public Earth Ocean Space scientific service records.',
        'status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=write_headers,json={'label':'Science Fabric','scopes':['data:read'],'created_by':'admin'})
    return issued.json()['api_key']


def test_release_readiness_and_migration(client):
    assert any(version == '0016' for version,_ in MIGRATIONS)
    health=client.get('/health').json()
    assert health['version']=='2.23.0'
    assert health['earth_ocean_space_scientific_service_fabric'] is True
    ready=client.get('/v1/scientific-fabric/readiness').json()
    assert ready['release']=='2.23.0'
    assert ready['migration_0016_applied'] is True
    assert ready['domains']==['earth','ocean','space']
    assert ready['truth_precedence']=='none'
    assert ready['automatic_cross_domain_blending'] is False


def test_ocean_record_routes_to_ocean_front_door(client, write_headers):
    add_record(client,rid='ocean-1',source_id='noaa-ncei',connector_id='noaa.ncei-data',discipline='oceanography',title='Global sea surface temperature',keywords=['ocean','sea surface temperature'],variables=['salinity'])
    r=client.post('/v1/scientific-fabric/materialize',headers=write_headers); assert r.status_code==200
    ocean=client.get('/v1/scientific-fabric/domains/ocean').json()
    assert ocean['records']==1
    assert ocean['truth_precedence']=='none'
    records=client.get('/v1/scientific-fabric/domains/ocean/records').json()
    assert records['items'][0]['id']=='ocean-1'
    earth=client.get('/v1/scientific-fabric/domains/earth/records').json()
    assert earth['total']==0


def test_space_record_routes_to_space_with_mission(client, write_headers):
    add_record(client,rid='space-1',source_id='mast',connector_id='mast.observations',discipline='astronomy',title='JWST exoplanet observation',mission='JWST',target='TRAPPIST-1',keywords=['exoplanet'])
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    summary=client.get('/v1/scientific-fabric/domains/space').json()
    assert summary['records']==1
    assert summary['missions']['JWST']==1
    assert summary['subdomains']['exoplanets']==1


def test_earth_record_routes_to_earth(client, write_headers):
    add_record(client,rid='earth-1',source_id='nasa-earthdata',connector_id='nasa.cmr-collections',discipline='earth_science',title='Land surface temperature Earth observation',keywords=['earth observation','land surface'],variables=['temperature'])
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    summary=client.get('/v1/scientific-fabric/domains/earth').json()
    assert summary['records']==1
    assert summary['subdomains']['earth-observation']==1


def test_classification_binding_is_routing_only(client, write_headers):
    add_record(client,rid='route-1',source_id='mast',connector_id='mast.observations',discipline='astronomy',title='Telescope observation',mission='HST')
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    with client.app.state.database.session_factory() as db:
        row=db.query(ScientificDomainBinding).filter(ScientificDomainBinding.subject_id=='route-1').one()
        assert row.routing_only is True
        assert row.truth_precedence=='none'
        assert row.classification_basis in {'explicit-discipline','metadata-keyword'}


def test_materialize_is_idempotent(client, write_headers):
    add_record(client,rid='idem-1',source_id='noaa-ncei',connector_id='noaa.ncei-data',discipline='oceanography',title='Ocean salinity')
    first=client.post('/v1/scientific-fabric/materialize',headers=write_headers); assert first.status_code==200
    second=client.post('/v1/scientific-fabric/materialize',headers=write_headers); assert second.status_code==200
    with client.app.state.database.session_factory() as db:
        rows=db.query(ScientificDomainBinding).filter(ScientificDomainBinding.subject_id=='idem-1').all()
        assert len(rows)==1


def test_assets_inherit_domain_from_scientific_record(client, write_headers):
    add_record(client,rid='asset-space',source_id='mast',connector_id='mast.observations',discipline='astronomy',title='JWST FITS observation',mission='JWST')
    with client.app.state.database.session_factory() as db:
        db.add(ScientificDataAsset(id='asset-1',scientific_record_id='asset-space',source_id='mast',connector_id='mast.observations',raw_record_id=None,dataset_id='dataset-asset-space',title='JWST FITS',asset_role='data',media_type='application/fits',format='fits',href='https://example.test/jwst.fits',storage_mode='remote',size_bytes=None,checksum=None,stac_roles_json=['data'],variables_json=[],spatial_extent_json=[],temporal_extent_json=[],license_name='public',attribution='MAST',metadata_json={},public=True)); db.commit()
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    body=client.get('/v1/scientific-fabric/domains/space/assets').json()
    assert body['total']==1 and body['items'][0]['id']=='asset-1'


def test_time_series_routes_without_rewriting_series_domain(client, write_headers):
    with client.app.state.database.session_factory() as db:
        db.add(TimeSeriesDefinition(id='ocean-series',source_id='noaa-ncei',connector_id='noaa.ncei-data',metric='sea_surface_temperature',title='Sea surface temperature',description='Ocean surface observation',dataset_id='sst',domain='oceanography',unit='degC',frequency='daily',geography_code=None,dimensions_json={},dimension_hash='x'*64,license_name='public',attribution='NOAA',public=True)); db.commit()
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    body=client.get('/v1/scientific-fabric/domains/ocean/timeseries').json()
    assert body['total']==1
    assert body['items'][0]['domain']=='oceanography'


def test_map_layer_routes_to_earth(client, write_headers):
    with client.app.state.database.session_factory() as db:
        db.add(MapLayer(id='earth-layer',source_id='nasa-earthdata',connector_id='nasa.gibs-wmts',external_layer_id='LST',title='Land Surface Temperature',description='Earth observation raster',layer_type='wmts',endpoint_url='https://example.test/wmts',tile_template=None,style_json={},bounds_json=[-180,-90,180,90],min_zoom=0,max_zoom=9,time_enabled=True,license_name='public',attribution='NASA',status='active',public=True,metadata_json={'domain':'earth observation'})); db.commit()
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    body=client.get('/v1/scientific-fabric/domains/earth/map-layers').json()
    assert body['total']==1 and body['items'][0]['id']=='earth-layer'


def test_zero_records_does_not_mean_no_science(client):
    body=client.get('/v1/scientific-fabric/domains/ocean').json()
    assert body['records']==0
    assert body['zero_records_implication']=='no-routed-records-not-no-science'


def test_public_domain_routes_are_scoped(client, write_headers):
    add_record(client,rid='public-space',source_id='mast',connector_id='mast.observations',discipline='astronomy',title='Public astronomy record')
    client.post('/v1/scientific-fabric/materialize',headers=write_headers)
    key=public_key(client,write_headers); headers={'Authorization':f'Bearer {key}'}
    root=client.get('/api/v1/scientific-fabric/domains',headers=headers); assert root.status_code==200
    records=client.get('/api/v1/scientific-fabric/domains/space/records',headers=headers); assert records.status_code==200
    assert records.json()['meta']['api_version']=='v1'


def test_unknown_domain_is_404(client):
    assert client.get('/v1/scientific-fabric/domains/underworld').status_code==404


def test_public_sdk_scientific_domain_helpers(monkeypatch):
    import httpx
    from sc_platform_core_public.client import PublicApiClient
    calls=[]
    class Response:
        is_error=False
        def json(self): return {'data': []}
    def fake_request(method,url,**kwargs): calls.append((method,url,kwargs)); return Response()
    monkeypatch.setattr(httpx,'request',fake_request)
    sdk=PublicApiClient('https://core.example','test-key')
    sdk.scientific_domains(); sdk.scientific_domain('ocean'); sdk.scientific_domain_records('space',mission='JWST'); sdk.scientific_domain_assets('earth')
    assert calls[0][1].endswith('/api/v1/scientific-fabric/domains')
    assert calls[1][1].endswith('/api/v1/scientific-fabric/domains/ocean')
    assert calls[2][2]['params']=={'mission':'JWST'}
    assert calls[3][1].endswith('/api/v1/scientific-fabric/domains/earth/assets')
