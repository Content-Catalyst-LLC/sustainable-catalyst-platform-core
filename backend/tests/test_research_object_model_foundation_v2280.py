from __future__ import annotations

from app.migrations import MIGRATIONS


def _public_key(client, write_headers):
    application = client.post('/v1/developer/applications', headers=write_headers, json={
        'name': 'Research Object Test', 'owner_name': 'Tester', 'owner_email': 'research-objects@example.com',
        'organization': 'Test', 'website_url': 'https://example.com',
        'use_case': 'Read public research object metadata.',
        'status': 'approved', 'plan_id': 'free', 'metadata': {}, 'actor': 'admin',
    })
    assert application.status_code in (200, 201), application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={'label': 'Research objects', 'scopes': ['data:read'], 'created_by': 'admin'},
    )
    assert issued.status_code in (200, 201), issued.text
    return issued.json()['api_key']


def _create(client, write_headers, object_type, name, attributes=None, visibility='public'):
    response = client.post('/v1/research-objects', headers=write_headers, json={
        'object_type': object_type,
        'name': name,
        'visibility': visibility,
        'attributes': attributes or {},
        'metadata': {'test': True},
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_v2280_migration_health_meta_and_readiness(client):
    assert any(version == '0031' for version, _ in MIGRATIONS)
    health = client.get('/health').json()
    assert health['version'] == '2.35.0'
    assert health['research_object_model_foundation'] is True
    meta = client.get('/v1/meta').json()
    for capability in {
        'research_object_model_foundation',
        'research_project_registry',
        'research_model_registry',
        'immutable_model_versions',
        'research_variables_and_parameters',
        'scenario_registry',
        'model_run_orchestration_records',
        'research_result_registry',
        'graph_native_research_objects',
        'lab_workbench_execution_boundary',
    }:
        assert capability in meta['capabilities']
    ready = client.get('/v1/research-objects/readiness').json()
    assert ready['migration_0031_applied'] is True
    assert ready['enabled'] is True
    assert ready['model_execution_by_core'] is False
    assert ready['visual_renderer_in_core'] is False
    assert set(ready['model_execution_targets']) == {'lab', 'workbench', 'external'}
    assert set(ready['object_types']) == {
        'research-project', 'model', 'model-version', 'variable',
        'parameter', 'scenario', 'model-run', 'result',
    }


def test_end_to_end_research_object_graph_and_bundle(client, write_headers):
    project = _create(client, write_headers, 'research-project', 'Grid transition study', {
        'research_question': 'How do cost, reliability, and emissions interact?',
        'objective': 'Explore transition tradeoffs.',
        'methodology': 'Scenario modeling',
        'owner_product': 'workspace',
        'lifecycle_state': 'active',
    })
    model = _create(client, write_headers, 'model', 'Grid transition model', {
        'project_entity_id': project['id'],
        'model_kind': 'simulation',
        'execution_target': 'lab',
        'specification': {'family': 'stock-flow'},
        'assumptions': ['bounded demand growth'],
    })
    version = _create(client, write_headers, 'model-version', 'Grid transition model v1', {
        'model_entity_id': model['id'],
        'version_label': '1.0.0',
        'code_version': 'git:abc123',
        'specification': {'equations': ['E = D * I']},
    })
    variable = _create(client, write_headers, 'variable', 'Annual electricity demand', {
        'model_entity_id': model['id'],
        'symbol': 'D',
        'role': 'input',
        'data_type': 'number',
        'unit': 'TWh/year',
        'uncertainty': {'type': 'interval', 'low': 100, 'high': 140},
    })
    parameter = _create(client, write_headers, 'parameter', 'Demand growth', {
        'model_entity_id': model['id'],
        'variable_entity_id': variable['id'],
        'name': 'demand_growth',
        'unit': '%/year',
        'default_value': 2.0,
        'bounds': {'min': -2.0, 'max': 8.0},
    })
    scenario = _create(client, write_headers, 'scenario', 'Rapid electrification', {
        'project_entity_id': project['id'],
        'scenario_state': 'ready',
        'parameter_values': {parameter['id']: 4.5},
        'assumptions': ['accelerated transport electrification'],
    })
    run = _create(client, write_headers, 'model-run', 'Rapid electrification run 001', {
        'model_version_entity_id': version['id'],
        'scenario_entity_id': scenario['id'],
        'executor_product': 'lab',
        'external_run_id': 'lab-run-001',
        'run_status': 'completed',
        'parameter_values': {parameter['id']: 4.5},
        'runtime': {'engine': 'python'},
    })
    result = _create(client, write_headers, 'result', 'Run 001 emissions summary', {
        'model_run_entity_id': run['id'],
        'result_kind': 'summary',
        'value': [41.2, 39.8, 38.7],
        'summary': 'Illustrative test result.',
        'quality_status': 'reviewed',
        'uncertainty': {'type': 'interval', 'low': 38.1, 'high': 45.0},
    })

    assert version['attributes']['specification_hash']
    assert len(version['attributes']['specification_hash']) == 64
    assert run['attributes']['executor_product'] == 'lab'
    assert parameter['attributes']['default_value'] == 2.0
    assert result['attributes']['value'] == [41.2, 39.8, 38.7]
    assert result['attributes']['model_run_entity_id'] == run['id']

    bundle = client.get(f"/v1/research-objects/projects/{project['id']}/bundle")
    assert bundle.status_code == 200, bundle.text
    body = bundle.json()
    assert body['total_objects'] == 8
    assert len(body['objects']['model']) == 1
    assert len(body['objects']['model-version']) == 1
    assert len(body['objects']['variable']) == 1
    assert len(body['objects']['parameter']) == 1
    assert len(body['objects']['scenario']) == 1
    assert len(body['objects']['model-run']) == 1
    assert len(body['objects']['result']) == 1

    model_edges = client.get('/v1/relationships', params={'subject_id': model['id']}).json()['items']
    assert any(edge['predicate'] == 'part_of' and edge['object_id'] == project['id'] for edge in model_edges)
    version_edges = client.get('/v1/relationships', params={'subject_id': version['id']}).json()['items']
    assert any(edge['predicate'] == 'version_of' and edge['object_id'] == model['id'] for edge in version_edges)
    result_edges = client.get('/v1/relationships', params={'subject_id': result['id']}).json()['items']
    assert any(edge['predicate'] == 'derived_from' and edge['object_id'] == run['id'] for edge in result_edges)

    stats = client.get('/v1/stats').json()
    assert stats['research_projects'] == 1
    assert stats['research_models'] == 1
    assert stats['research_model_versions'] == 1
    assert stats['research_variables'] == 1
    assert stats['research_parameters'] == 1
    assert stats['research_scenarios'] == 1
    assert stats['research_model_runs'] == 1
    assert stats['research_results'] == 1


def test_research_object_validation_boundaries(client, write_headers):
    project = _create(client, write_headers, 'research-project', 'Boundary project')
    bad = client.post('/v1/research-objects', headers=write_headers, json={
        'object_type': 'model-version',
        'name': 'Invalid model version',
        'attributes': {'model_entity_id': project['id'], 'version_label': 'bad'},
    })
    assert bad.status_code == 422
    assert 'must reference entity type: model' in bad.text

    model = _create(client, write_headers, 'model', 'External-only model', {
        'project_entity_id': project['id'],
        'model_kind': 'mathematical',
        'execution_target': 'workbench',
    })
    assert model['attributes']['execution_target'] == 'workbench'

    other_project = _create(client, write_headers, 'research-project', 'Other boundary project')
    foreign_scenario = _create(client, write_headers, 'scenario', 'Foreign scenario', {
        'project_entity_id': other_project['id'],
    })
    version = _create(client, write_headers, 'model-version', 'Boundary model v1', {
        'model_entity_id': model['id'],
        'version_label': '1.0.0',
    })
    bad_run = client.post('/v1/research-objects', headers=write_headers, json={
        'object_type': 'model-run',
        'name': 'Cross-project run',
        'attributes': {
            'model_version_entity_id': version['id'],
            'scenario_entity_id': foreign_scenario['id'],
            'executor_product': 'workbench',
        },
    })
    assert bad_run.status_code == 422
    assert "model's research project" in bad_run.text

    base_foreign = client.post('/v1/research-objects', headers=write_headers, json={
        'object_type': 'scenario',
        'name': 'Cross-project derived scenario',
        'attributes': {
            'project_entity_id': project['id'],
            'base_scenario_entity_id': foreign_scenario['id'],
        },
    })
    assert base_foreign.status_code == 422
    assert 'same research project' in base_foreign.text

    ready = client.get('/v1/research-objects/readiness').json()
    assert ready['model_execution_by_core'] is False


def test_public_api_exposes_only_public_research_metadata(client, write_headers):
    public_project = _create(client, write_headers, 'research-project', 'Public project', visibility='public')
    private_project = _create(client, write_headers, 'research-project', 'Private project', visibility='private')
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    ready = client.get('/api/v1/research-objects/readiness', headers=headers)
    assert ready.status_code == 200, ready.text
    assert ready.json()['data']['model_execution_by_core'] is False
    listed = client.get('/api/v1/research-objects?object_type=research-project', headers=headers)
    assert listed.status_code == 200, listed.text
    ids = {row['id'] for row in listed.json()['data']}
    assert public_project['id'] in ids
    assert private_project['id'] not in ids
    assert client.get(f"/api/v1/research-objects/{public_project['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/research-objects/{private_project['id']}", headers=headers).status_code == 404


def test_public_research_metadata_can_be_disabled(client, write_headers):
    key = _public_key(client, write_headers)
    headers = {'Authorization': f'Bearer {key}'}
    object.__setattr__(client.app.state.settings, 'research_object_public_metadata_enabled', False)
    assert client.get('/api/v1/research-objects/readiness', headers=headers).status_code == 404
    assert client.get('/api/v1/research-objects', headers=headers).status_code == 404
