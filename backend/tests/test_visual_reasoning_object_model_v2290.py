from __future__ import annotations

from app.migrations import MIGRATIONS


def _public_key(client, write_headers):
    application = client.post('/v1/developer/applications', headers=write_headers, json={
        'name': 'Visual Reasoning Test', 'owner_name': 'Tester', 'owner_email': 'visual-reasoning@example.com',
        'organization': 'Test', 'website_url': 'https://example.com',
        'use_case': 'Read public visual reasoning metadata.',
        'status': 'approved', 'plan_id': 'free', 'metadata': {}, 'actor': 'admin',
    })
    assert application.status_code in (200, 201), application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={'label': 'Visual reasoning', 'scopes': ['data:read'], 'created_by': 'admin'},
    )
    assert issued.status_code in (200, 201), issued.text
    return issued.json()['api_key']


def _research(client, write_headers, object_type, name, attributes=None, visibility='public'):
    r = client.post('/v1/research-objects', headers=write_headers, json={
        'object_type': object_type, 'name': name, 'visibility': visibility,
        'attributes': attributes or {}, 'metadata': {'visual_test': True},
    })
    assert r.status_code == 200, r.text
    return r.json()


def _visual(client, write_headers, name, *, project=None, subject=None, visibility='public', kind='system-map'):
    r = client.post('/v1/visual-reasoning/objects', headers=write_headers, json={
        'name': name,
        'visibility': visibility,
        'visual_kind': kind,
        'reasoning_purpose': 'explore',
        'semantic_state': 'draft',
        'coordinate_space': 'abstract',
        'project_entity_id': project,
        'primary_subject_entity_id': subject,
        'lens': {'focus': 'structure'},
        'filters': {},
        'assumptions': ['semantic structure precedes rendering'],
        'metadata': {'test': True},
    })
    assert r.status_code == 200, r.text
    return r.json()


def _child(client, write_headers, visual_id, child, data):
    r = client.post(f'/v1/visual-reasoning/objects/{visual_id}/{child}', headers=write_headers, json={'data': data})
    assert r.status_code == 200, r.text
    return r.json()


def test_v2290_migration_health_meta_and_readiness(client):
    assert any(version == '0032' for version, _ in MIGRATIONS)
    health = client.get('/health').json()
    assert health['version'] == '2.37.0.2'
    assert health['visual_reasoning_object_model'] is True
    meta = client.get('/v1/meta').json()
    for capability in {
        'visual_reasoning_object_model',
        'renderer_neutral_visual_semantics',
        'visual_semantic_elements_and_relations',
        'visual_reasoning_layers',
        'visual_annotations_and_caveats',
        'source_entity_and_scientific_object_bindings',
        'immutable_visual_semantic_snapshots',
        'visual_snapshot_sha256_integrity',
        'visualization_specification_renderer_registry',
    }:
        assert capability in meta['capabilities']
    ready = client.get('/v1/visual-reasoning/readiness').json()
    assert ready['migration_0032_applied'] is True
    assert ready['enabled'] is True
    assert ready['graph_native'] is True
    assert ready['renderer_neutral'] is True
    assert ready['renderer_registry_in_core'] is True
    assert ready['layout_engine_in_core'] is False
    assert ready['automatic_truth_promotion'] is False
    assert 'system-map' in ready['visual_kinds']
    assert 'scenario-landscape' in ready['visual_kinds']


def test_visual_reasoning_semantic_bundle_and_snapshot(client, write_headers):
    project = _research(client, write_headers, 'research-project', 'Grid visual study', {
        'research_question': 'How should the grid transition system be reasoned about visually?'
    })
    model = _research(client, write_headers, 'model', 'Grid model', {
        'project_entity_id': project['id'], 'model_kind': 'simulation', 'execution_target': 'lab'
    })
    scenario = _research(client, write_headers, 'scenario', 'High electrification', {
        'project_entity_id': project['id'], 'scenario_state': 'ready'
    })
    visual = _visual(client, write_headers, 'Grid transition system map', project=project['id'], subject=model['id'])
    assert visual['attributes']['visual_kind'] == 'system-map'
    assert visual['attributes']['project_entity_id'] == project['id']

    model_el = _child(client, write_headers, visual['id'], 'elements', {
        'element_key': 'model', 'element_kind': 'node', 'semantic_role': 'model',
        'label': 'Grid model', 'source_entity_id': model['id'],
        'uncertainty': {'known': False}, 'provenance': {'source': 'research-object'},
    })
    scenario_el = _child(client, write_headers, visual['id'], 'elements', {
        'element_key': 'scenario', 'element_kind': 'state', 'semantic_role': 'scenario',
        'label': 'High electrification', 'source_entity_id': scenario['id'],
    })
    relation = _child(client, write_headers, visual['id'], 'relations', {
        'source_element_id': scenario_el['id'], 'target_element_id': model_el['id'],
        'relation_kind': 'dependency', 'direction': 'directed', 'confidence': 0.9,
        'provenance': {'basis': 'scenario-model binding'},
    })
    layer = _child(client, write_headers, visual['id'], 'layers', {
        'layer_key': 'model-structure', 'name': 'Model structure', 'layer_kind': 'model',
        'order_index': 10, 'visible_by_default': True,
    })
    annotation = _child(client, write_headers, visual['id'], 'annotations', {
        'element_id': model_el['id'], 'annotation_kind': 'caveat',
        'text': 'This object expresses semantics, not renderer coordinates.',
    })
    snap = client.post(f"/v1/visual-reasoning/objects/{visual['id']}/snapshots", headers=write_headers, json={
        'snapshot_key': 'baseline-v1', 'created_by': 'tester', 'provenance': {'reason': 'release-test'}
    })
    assert snap.status_code == 200, snap.text
    assert len(snap.json()['state_hash']) == 64

    bundle = client.get(f"/v1/visual-reasoning/objects/{visual['id']}/bundle")
    assert bundle.status_code == 200, bundle.text
    body = bundle.json()
    assert len(body['elements']) == 2
    assert len(body['relations']) == 1
    assert len(body['layers']) == 1
    assert len(body['annotations']) == 1
    assert len(body['snapshots']) == 1
    assert body['relations'][0]['id'] == relation['id']
    assert body['layers'][0]['id'] == layer['id']
    assert body['annotations'][0]['id'] == annotation['id']
    assert body['renderer_contract']['renderer_neutral'] is True
    assert body['renderer_contract']['layout_engine_in_core'] is False
    assert body['renderer_contract']['visualization_specification_layer'].startswith('v2.36.0')
    assert body['renderer_contract']['renderer_execution_by_core'] is False

    edges = client.get('/v1/relationships', params={'subject_id': visual['id']}).json()['items']
    assert any(edge['predicate'] == 'part_of' and edge['object_id'] == project['id'] for edge in edges)
    assert any(edge['predicate'] == 'about' and edge['object_id'] == model['id'] for edge in edges)

    stats = client.get('/v1/stats').json()
    assert stats['visual_reasoning_objects'] == 1
    assert stats['visual_reasoning_elements'] == 2
    assert stats['visual_reasoning_relations'] == 1
    assert stats['visual_reasoning_layers'] == 1
    assert stats['visual_reasoning_annotations'] == 1
    assert stats['visual_reasoning_snapshots'] == 1


def test_visual_relation_cannot_cross_visual_objects(client, write_headers):
    a = _visual(client, write_headers, 'Visual A')
    b = _visual(client, write_headers, 'Visual B')
    a_el = _child(client, write_headers, a['id'], 'elements', {'element_key':'a','label':'A','semantic_role':'context'})
    b_el = _child(client, write_headers, b['id'], 'elements', {'element_key':'b','label':'B','semantic_role':'context'})
    bad = client.post(f"/v1/visual-reasoning/objects/{a['id']}/relations", headers=write_headers, json={'data':{
        'source_element_id': a_el['id'], 'target_element_id': b_el['id'], 'relation_kind':'association'
    }})
    assert bad.status_code == 422
    assert 'same visual reasoning object' in bad.text


def test_public_api_exposes_only_public_visual_objects(client, write_headers):
    public = _visual(client, write_headers, 'Public visual', visibility='public')
    private = _visual(client, write_headers, 'Private visual', visibility='private')
    _child(client, write_headers, public['id'], 'elements', {'element_key':'public-node','label':'Public node','semantic_role':'context'})
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    ready = client.get('/api/v1/visual-reasoning/readiness', headers=headers)
    assert ready.status_code == 200, ready.text
    assert ready.json()['data']['renderer_neutral'] is True
    listed = client.get('/api/v1/visual-reasoning/objects', headers=headers)
    assert listed.status_code == 200, listed.text
    ids = {row['id'] for row in listed.json()['data']}
    assert public['id'] in ids
    assert private['id'] not in ids
    assert client.get(f"/api/v1/visual-reasoning/objects/{public['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/visual-reasoning/objects/{private['id']}", headers=headers).status_code == 404
    bundle = client.get(f"/api/v1/visual-reasoning/objects/{public['id']}/bundle", headers=headers)
    assert bundle.status_code == 200, bundle.text
    assert len(bundle.json()['data']['elements']) == 1


def test_public_visual_metadata_can_be_disabled(client, write_headers):
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    object.__setattr__(client.app.state.settings, 'visual_reasoning_public_metadata_enabled', False)
    assert client.get('/api/v1/visual-reasoning/readiness', headers=headers).status_code == 404
    assert client.get('/api/v1/visual-reasoning/objects', headers=headers).status_code == 404
