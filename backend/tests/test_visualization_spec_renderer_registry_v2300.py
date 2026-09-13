from __future__ import annotations

from app.migrations import MIGRATIONS


def _visual(client, write_headers, name='Renderer registry visual', kind='system-map', visibility='public'):
    r = client.post('/v1/visual-reasoning/objects', headers=write_headers, json={
        'name': name,
        'visibility': visibility,
        'visual_kind': kind,
        'reasoning_purpose': 'explain',
        'semantic_state': 'draft',
        'coordinate_space': 'abstract',
        'lens': {}, 'filters': {}, 'assumptions': [], 'metadata': {'v230': True},
    })
    assert r.status_code == 200, r.text
    return r.json()


def _spec(client, write_headers, visual_id, *, spec_key='main', spec_kind='diagram', preferred=None, policy='compatible', revision=1):
    r = client.post('/v1/visualization/specifications', headers=write_headers, json={
        'visual_entity_id': visual_id,
        'spec_key': spec_key,
        'revision': revision,
        'spec_version': '1.0',
        'spec_kind': spec_kind,
        'title': 'Governed visualization specification',
        'preferred_renderer_key': preferred,
        'renderer_policy': policy,
        'encoding': {'nodes': {'label': 'label'}, 'edges': {'type': 'relation_kind'}},
        'interaction': {'zoom': True},
        'accessibility': {'text_summary_required': True},
        'layout_constraints': {'direction': 'left-to-right'},
        'export': {'formats': ['svg', 'png']},
        'metadata': {'test': True},
        'created_by': 'tester',
    })
    assert r.status_code == 200, r.text
    return r.json()


def _public_key(client, write_headers):
    app = client.post('/v1/developer/applications', headers=write_headers, json={
        'name': 'Visualization Registry Test', 'owner_name': 'Tester',
        'owner_email': 'visualization-registry@example.com', 'organization': 'Test',
        'website_url': 'https://example.com', 'use_case': 'Read renderer registry metadata.',
        'status': 'approved', 'plan_id': 'free', 'metadata': {}, 'actor': 'admin',
    })
    assert app.status_code in (200, 201), app.text
    issued = client.post(f"/v1/developer/applications/{app.json()['id']}/credentials", headers=write_headers, json={
        'label': 'Visualization registry', 'scopes': ['data:read'], 'created_by': 'admin',
    })
    assert issued.status_code in (200, 201), issued.text
    return issued.json()['api_key']


def test_v2300_migration_health_readiness_and_seeded_registry(client):
    assert any(version == '0033' for version, _ in MIGRATIONS)
    health = client.get('/health').json()
    assert health['version'] == '2.36.1.1'
    assert health['visualization_specification_renderer_registry'] is True
    ready = client.get('/v1/visualization/readiness').json()
    assert ready['release'] == '2.36.1.1'
    assert ready['migration_0033_applied'] is True
    assert ready['renderer_registry'] is True
    assert ready['renderer_execution_by_core'] is False
    assert ready['layout_execution_by_core'] is False
    assert ready['render_output_storage_by_core'] is False
    assert ready['selection_is_advisory'] is True
    assert ready['counts']['renderers'] == 4
    assert ready['counts']['renderer_versions'] == 4
    assert ready['counts']['compatibility_rules'] >= 10


def test_immutable_visualization_spec_hash_and_duplicate_revision(client, write_headers):
    visual = _visual(client, write_headers)
    spec = _spec(client, write_headers, visual['id'])
    assert len(spec['state_hash']) == 64
    assert spec['spec_kind'] == 'diagram'
    assert spec['revision'] == 1
    duplicate = client.post('/v1/visualization/specifications', headers=write_headers, json={
        'visual_entity_id': visual['id'], 'spec_key': 'main', 'revision': 1,
        'spec_kind': 'diagram', 'encoding': {}, 'interaction': {}, 'accessibility': {},
        'layout_constraints': {}, 'export': {}, 'metadata': {},
    })
    assert duplicate.status_code == 409, duplicate.text
    revision2 = _spec(client, write_headers, visual['id'], revision=2)
    assert revision2['state_hash'] != spec['state_hash']


def test_registry_resolution_is_deterministic_and_non_executing(client, write_headers):
    visual = _visual(client, write_headers, kind='system-map')
    spec = _spec(client, write_headers, visual['id'], spec_kind='diagram')
    resolved = client.post(f"/v1/visualization/specifications/{spec['id']}/resolve", headers=write_headers, json={'created_by':'tester'})
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body['resolution_state'] == 'resolved'
    assert body['resolved_renderer_key'] == 'contract.d3'
    assert body['resolved_renderer_version'] == 'contract-v1'
    assert body['execution_performed'] is False
    assert body['selection_mode'] == 'registry-priority'

    incompatible = client.post(f"/v1/visualization/specifications/{spec['id']}/resolve", headers=write_headers, json={
        'requested_renderer_key': 'contract.maplibre', 'created_by':'tester'
    })
    assert incompatible.status_code == 200, incompatible.text
    assert incompatible.json()['resolution_state'] == 'unresolved'
    assert incompatible.json()['execution_performed'] is False

    preferred_only = _spec(client, write_headers, visual['id'], spec_key='preferred-only', spec_kind='diagram', policy='preferred-only')
    unresolved = client.post(f"/v1/visualization/specifications/{preferred_only['id']}/resolve", headers=write_headers, json={'created_by':'tester'})
    assert unresolved.status_code == 200, unresolved.text
    assert unresolved.json()['resolution_state'] == 'unresolved'


def test_renderer_registry_exposes_contracts_not_installed_runtimes(client):
    r = client.get('/v1/visualization/renderers')
    assert r.status_code == 200, r.text
    items = r.json()['items']
    keys = {item['renderer_key'] for item in items}
    assert {'contract.d3', 'contract.vega-lite', 'contract.plotly', 'contract.maplibre'} <= keys
    for item in items:
        assert item['executable_by_core'] is False
        assert item['execution_mode'] == 'external-runtime'
        assert item['metadata_json']['installed_runtime_asserted'] is False


def test_public_api_hides_private_visual_specifications(client, write_headers):
    public_visual = _visual(client, write_headers, name='Public visual', visibility='public')
    private_visual = _visual(client, write_headers, name='Private visual', visibility='private')
    public_spec = _spec(client, write_headers, public_visual['id'], spec_key='public')
    private_spec = _spec(client, write_headers, private_visual['id'], spec_key='private')
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    ready = client.get('/api/v1/visualization/readiness', headers=headers)
    assert ready.status_code == 200, ready.text
    assert ready.json()['data']['renderer_execution_by_core'] is False
    renderers = client.get('/api/v1/visualization/renderers', headers=headers)
    assert renderers.status_code == 200, renderers.text
    assert len(renderers.json()['data']) == 4
    listed = client.get('/api/v1/visualization/specifications', headers=headers)
    assert listed.status_code == 200, listed.text
    ids = {row['id'] for row in listed.json()['data']}
    assert public_spec['id'] in ids
    assert private_spec['id'] not in ids


def test_custom_renderer_contract_registration_and_resolution_history(client, write_headers):
    rejected = client.post('/v1/visualization/renderers', headers=write_headers, json={
        'renderer_key':'custom.bad', 'name':'Bad renderer', 'executable_by_core':True,
    })
    assert rejected.status_code == 422, rejected.text

    created = client.post('/v1/visualization/renderers', headers=write_headers, json={
        'renderer_key':'contract.custom-diagram', 'name':'Custom diagram contract',
        'renderer_family':'custom-diagram', 'runtime':'external-runtime', 'execution_mode':'external-runtime',
        'executable_by_core':False, 'supported_spec_versions':['1.0'],
        'capabilities':{'diagram':True}, 'metadata':{'installed_runtime_asserted':False},
    })
    assert created.status_code == 200, created.text
    version = client.post('/v1/visualization/renderers/contract.custom-diagram/versions', headers=write_headers, json={
        'version':'contract-v1', 'contract_version':'1.0', 'status':'active'
    })
    assert version.status_code == 200, version.text
    rule = client.post('/v1/visualization/renderers/contract.custom-diagram/compatibility-rules', headers=write_headers, json={
        'visual_kind':'system-map', 'spec_kind':'diagram', 'priority':500,
        'required_capabilities':['diagram']
    })
    assert rule.status_code == 200, rule.text

    visual = _visual(client, write_headers, name='Custom renderer visual', kind='system-map')
    spec = _spec(client, write_headers, visual['id'], spec_key='custom-resolution', spec_kind='diagram')
    resolution = client.post(f"/v1/visualization/specifications/{spec['id']}/resolve", headers=write_headers, json={'created_by':'tester'})
    assert resolution.status_code == 200, resolution.text
    assert resolution.json()['resolved_renderer_key'] == 'contract.custom-diagram'
    assert resolution.json()['execution_performed'] is False
    history = client.get(f"/v1/visualization/specifications/{spec['id']}/resolutions")
    assert history.status_code == 200, history.text
    assert len(history.json()['items']) == 1
    assert history.json()['items'][0]['resolved_renderer_key'] == 'contract.custom-diagram'
