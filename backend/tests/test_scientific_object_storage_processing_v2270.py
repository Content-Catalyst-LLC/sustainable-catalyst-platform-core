from __future__ import annotations

from pathlib import Path

from app.migrations import MIGRATIONS
from app.models import ScientificProcessingAdapter, ScientificStoredObject


def _public_key(client, write_headers):
    application = client.post('/v1/developer/applications', headers=write_headers, json={
        'name': 'Scientific Object Test', 'owner_name': 'Tester', 'owner_email': 'scientific-objects@example.com',
        'organization': 'Test', 'website_url': 'https://example.com',
        'use_case': 'Read public scientific object metadata.',
        'status': 'approved', 'plan_id': 'free', 'metadata': {}, 'actor': 'admin',
    })
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={'label': 'Scientific objects', 'scopes': ['data:read'], 'created_by': 'admin'},
    )
    return issued.json()['api_key']


def test_v2270_migration_health_meta_and_seeded_contracts(client):
    assert any(version == '0030' for version, _ in MIGRATIONS)
    health = client.get('/health').json()
    assert health['version'] == '2.35.0'
    assert health['scientific_object_storage_processing_adapter_fabric'] is True
    meta = client.get('/v1/meta').json()
    for capability in {
        'scientific_object_storage_processing_adapter_fabric',
        'scientific_storage_backend_registry',
        'scientific_object_integrity_hashing',
        'scientific_derived_object_lineage',
        'scientific_processing_adapter_registry',
        'builtin_scientific_object_manifest_adapter',
    }:
        assert capability in meta['capabilities']
    ready = client.get('/v1/scientific-objects/readiness').json()
    assert ready['migration_0030_applied'] is True
    assert ready['local_storage_ready'] is True
    assert ready['processing_adapters'] == 4
    assert ready['executable_adapters'] == 1
    adapters = client.get('/v1/scientific-objects/adapters').json()['items']
    by_key = {item['adapter_key']: item for item in adapters}
    assert by_key['builtin.object-manifest']['executable'] is True
    assert by_key['external.xarray']['executable'] is False
    assert by_key['external.gdal']['execution_mode'] == 'external-contract'


def test_local_upload_integrity_content_and_manifest_processing(client, write_headers):
    content = b'CDF\x01sustainable-catalyst-test-object\n'
    uploaded = client.put(
        '/v1/scientific-objects/upload/netcdf?title=Climate%20cube&public=true',
        headers={**write_headers, 'content-type': 'application/x-netcdf'},
        content=content,
    )
    assert uploaded.status_code == 200, uploaded.text
    obj = uploaded.json()
    assert obj['backend_key'] == 'local-filesystem'
    assert obj['format'] == 'netcdf'
    assert obj['integrity_status'] == 'verified'
    assert obj['size_bytes'] == len(content)
    assert len(obj['content_hash']) == 64
    assert obj['canonical_uri'].startswith('sc-object://local-filesystem/sha256/')

    fetched = client.get(f"/v1/scientific-objects/{obj['id']}/content")
    assert fetched.status_code == 200
    assert fetched.content == content

    first = client.post('/v1/scientific-objects/process', headers=write_headers, json={
        'input_object_id': obj['id'],
        'adapter_key': 'builtin.object-manifest',
        'operation': 'manifest',
        'idempotency_key': 'manifest-1',
        'parameters': {'purpose': 'test'},
        'requested_by': 'pytest',
    })
    assert first.status_code == 200, first.text
    run = first.json()
    assert run['state'] == 'completed'
    assert run['output_object_id']
    output = client.get(f"/v1/scientific-objects/{run['output_object_id']}").json()
    assert output['derived'] is True
    assert output['parent_object_id'] == obj['id']
    assert output['format'] == 'json'

    second = client.post('/v1/scientific-objects/process', headers=write_headers, json={
        'input_object_id': obj['id'], 'adapter_key': 'builtin.object-manifest', 'operation': 'manifest',
        'idempotency_key': 'manifest-1', 'parameters': {'purpose': 'different-but-idempotent'}, 'requested_by': 'pytest',
    })
    assert second.status_code == 200
    assert second.json()['id'] == run['id']


def test_external_references_are_credential_free_and_not_fetched(client, write_headers):
    ok = client.post('/v1/scientific-objects/register-reference', headers=write_headers, json={
        'uri': 's3://science-bucket/earth/temperature.zarr',
        'title': 'Provider managed temperature cube',
        'format': 'zarr',
        'size_bytes': 123456,
        'content_hash': 'a' * 64,
        'checksum_algorithm': 'sha256',
        'public': True,
        'created_by': 'pytest',
    })
    assert ok.status_code == 200, ok.text
    obj = ok.json()
    assert obj['backend_key'] == 'external-reference'
    assert obj['integrity_status'] == 'declared'
    content = client.get(f"/v1/scientific-objects/{obj['id']}/content")
    assert content.status_code == 422
    assert 'not fetched by Platform Core' in content.text

    signed = client.post('/v1/scientific-objects/register-reference', headers=write_headers, json={
        'uri': 'https://example.test/data.nc?token=secret', 'title': 'Bad signed URL', 'format': 'netcdf'
    })
    assert signed.status_code == 422
    assert 'Signed/query-bearing' in signed.text


def test_public_api_exposes_metadata_not_object_bytes(client, write_headers):
    uploaded = client.put(
        '/v1/scientific-objects/upload/fits?title=Public%20FITS&public=true',
        headers={**write_headers, 'content-type': 'application/fits'},
        content=b'SIMPLE  =                    T',
    ).json()
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    ready = client.get('/api/v1/scientific-objects/readiness', headers=headers)
    assert ready.status_code == 200
    listed = client.get('/api/v1/scientific-objects', headers=headers)
    assert listed.status_code == 200
    ids = {item['id'] for item in listed.json()['data']}
    assert uploaded['id'] in ids
    assert client.get(f"/api/v1/scientific-objects/{uploaded['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/scientific-objects/{uploaded['id']}/content", headers=headers).status_code == 404


def test_contract_only_adapter_cannot_execute(client, write_headers):
    obj = client.put(
        '/v1/scientific-objects/upload/netcdf?title=Input',
        headers={**write_headers, 'content-type': 'application/x-netcdf'},
        content=b'netcdf-test',
    ).json()
    response = client.post('/v1/scientific-objects/process', headers=write_headers, json={
        'input_object_id': obj['id'], 'adapter_key': 'external.xarray', 'operation': 'subset',
        'idempotency_key': 'no-exec', 'parameters': {}, 'requested_by': 'pytest',
    })
    assert response.status_code == 422
    assert 'not executable' in response.text


def test_public_metadata_surface_can_be_disabled(client, write_headers):
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    object.__setattr__(client.app.state.settings, "scientific_object_public_metadata_enabled", False)
    assert client.get('/api/v1/scientific-objects/readiness', headers=headers).status_code == 404
    assert client.get('/api/v1/scientific-objects', headers=headers).status_code == 404
    assert client.get('/api/v1/scientific-objects/adapters', headers=headers).status_code == 404
