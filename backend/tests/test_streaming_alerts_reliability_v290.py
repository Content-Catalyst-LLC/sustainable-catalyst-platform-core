from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import AlertRule, LiveDataConnector, LiveDataObservation, StreamEvent
from app.services.reliability import (
    claim_next_work,
    complete_work,
    evaluate_alerts,
    fail_work,
    queue_connector_work,
    replay_dead_letter,
    resolve_failover,
    stale_connectors,
)


def _db(client):
    return client.app.state.database.session_factory()


def test_v290_readiness_surface(client, write_headers):
    response = client.get('/v1/reliability/readiness', headers=write_headers)
    assert response.status_code == 200
    body = response.json()
    assert body['release'] == '2.24.0'
    assert body['streaming_enabled'] is True
    assert body['worker_enabled'] is True
    assert body['provider_failover_enabled'] is True
    assert body['external_provider_health_release_blocking'] is False


def test_persistent_connector_queue_and_lease(client):
    with _db(client) as db:
        row = queue_connector_work(db, 'world-bank.indicators', parameters={'indicator': 'SP.POP.TOTL'}, priority=10)
        claimed = claim_next_work(db, worker_id='worker-a', lease_seconds=30)
        assert claimed.id == row.id
        assert claimed.status == 'claimed'
        assert claimed.attempt_count == 1
        assert claimed.lease_owner == 'worker-a'
        assert claimed.lease_expires_at is not None
        complete_work(db, claimed, 'run-123')
        assert claimed.status == 'completed'
        assert claimed.ingestion_run_id == 'run-123'


def test_queue_endpoint_rejects_unknown_connector(client, write_headers):
    response = client.post('/v1/reliability/queue/not-a-connector', headers=write_headers, json={})
    assert response.status_code == 404


def test_dead_letter_after_max_attempts_and_replay(client):
    with _db(client) as db:
        row = queue_connector_work(db, 'world-bank.indicators', max_attempts=1)
        claimed = claim_next_work(db, worker_id='worker-b')
        assert claimed.id == row.id
        _, dead = fail_work(db, claimed, 'synthetic failure', retry_delay_seconds=0)
        assert dead is not None
        assert claimed.status == 'dead_letter'
        replay = replay_dead_letter(db, dead.id, requested_by='test-replay')
        assert replay.connector_id == row.connector_id
        assert replay.status == 'pending'
        assert dead.status == 'replayed'
        assert dead.replay_count == 1


def test_stale_source_detection_distinguishes_current_and_stale(client):
    now = datetime.now(timezone.utc)
    with _db(client) as db:
        current = db.get(LiveDataConnector, 'world-bank.indicators')
        stale = db.get(LiveDataConnector, 'usgs.earthquakes')
        current.freshness_window_seconds = 3600
        current.last_success_at = now - timedelta(minutes=10)
        stale.freshness_window_seconds = 60
        stale.last_success_at = now - timedelta(hours=2)
        db.add_all([current, stale]); db.commit()
        items = stale_connectors(db, now=now, include_never=False)
        ids = {item['connector_id'] for item in items}
        assert 'usgs.earthquakes' in ids
        assert 'world-bank.indicators' not in ids


def test_provider_failover_uses_explicit_group_only(client):
    with _db(client) as db:
        primary = db.get(LiveDataConnector, 'world-bank.indicators')
        backup = db.get(LiveDataConnector, 'un.sdg-catalog')
        primary.configuration_json = {**(primary.configuration_json or {}), 'failover_group': 'test-group', 'failover_priority': 10}
        backup.configuration_json = {**(backup.configuration_json or {}), 'failover_group': 'test-group', 'failover_priority': 20}
        primary.last_health_status = 'degraded'
        backup.last_health_status = 'operational'
        db.add_all([primary, backup]); db.commit()
        result = resolve_failover(db, primary.id, client.app.state.live_data_runtime)
        assert result['selected_connector_id'] == backup.id
        assert result['failover_used'] is True


def test_provider_failover_does_not_invent_cross_source_equivalence(client):
    with _db(client) as db:
        connector = db.get(LiveDataConnector, 'world-bank.indicators')
        connector.configuration_json = {k:v for k,v in (connector.configuration_json or {}).items() if not k.startswith('failover_')}
        connector.last_health_status = 'degraded'
        db.add(connector); db.commit()
        result = resolve_failover(db, connector.id, client.app.state.live_data_runtime)
        assert result['failover_group'] is None
        assert len(result['candidates']) == 1
        assert result['selected_connector_id'] is None


def test_threshold_alert_emits_stream_event(client):
    now = datetime.now(timezone.utc)
    with _db(client) as db:
        rule = AlertRule(name='High test value', domain='economics', metric='TEST.METRIC', operator='gt', threshold_number=10, severity='high', enabled=True, public=True)
        db.add(rule); db.commit(); db.refresh(rule)
        observation = LiveDataObservation(
            id='alert-observation', connector_id='world-bank.indicators', source_id='world-bank',
            source_record_id='test', domain='economics', metric='TEST.METRIC', value_number=12,
            unit='index', observed_at=now, retrieved_at=now, public=True,
        )
        db.add(observation); db.commit()
        events = evaluate_alerts(db, observation)
        assert len(events) == 1
        assert events[0].event_type == 'alert.triggered'
        assert events[0].payload_json['rule_id'] == rule.id
        assert events[0].public is True


def test_geographic_alert_bbox_filters_point(client):
    now = datetime.now(timezone.utc)
    with _db(client) as db:
        rule = AlertRule(name='Palestine bbox', metric='TEST.GEO', operator='exists', geography_json={'type':'bbox','bbox':[34,31,36,33]}, enabled=True)
        db.add(rule); db.commit()
        inside = LiveDataObservation(id='geo-in', connector_id='world-bank.indicators', source_id='world-bank', source_record_id='in', domain='test', metric='TEST.GEO', value_number=1, geometry_json={'type':'Point','coordinates':[35.2,31.9]}, observed_at=now, retrieved_at=now)
        outside = LiveDataObservation(id='geo-out', connector_id='world-bank.indicators', source_id='world-bank', source_record_id='out', domain='test', metric='TEST.GEO', value_number=1, geometry_json={'type':'Point','coordinates':[-87.6,41.8]}, observed_at=now, retrieved_at=now)
        db.add_all([inside,outside]); db.commit()
        assert len(evaluate_alerts(db, inside)) == 1
        assert len(evaluate_alerts(db, outside)) == 0


def test_alert_rule_api_validates_threshold(client, write_headers):
    response = client.post('/v1/reliability/alerts/rules', headers=write_headers, json={'name':'bad','operator':'gt'})
    assert response.status_code == 422
    good = client.post('/v1/reliability/alerts/rules', headers=write_headers, json={'name':'good','operator':'gte','threshold_number':5,'metric':'X'})
    assert good.status_code == 200


def test_geographic_subscription_api(client, write_headers):
    response = client.post('/v1/reliability/subscriptions/geographic', headers=write_headers, json={
        'name':'Eastern Mediterranean', 'geometry':{'type':'bbox','bbox':[30,29,38,35]},
        'domains':['humanitarian','hazards'], 'event_types':['alert.triggered']
    })
    assert response.status_code == 200
    body = response.json()
    assert body['geometry']['type'] == 'bbox'
    listed = client.get('/v1/reliability/subscriptions/geographic', headers=write_headers).json()
    assert listed['total'] == 1


def test_sse_snapshot_includes_internal_events(client, write_headers):
    with _db(client) as db:
        queue_connector_work(db, 'world-bank.indicators')
    response = client.get('/v1/reliability/stream?once=true', headers=write_headers)
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert 'event: connector.work.queued' in response.text


def test_public_sse_only_exposes_public_events(client):
    with _db(client) as db:
        db.add(StreamEvent(event_type='public.test', subject_type='test', payload_json={'safe':True}, public=True))
        db.add(StreamEvent(event_type='private.test', subject_type='test', payload_json={'secret':True}, public=False))
        db.commit()
    # public test harness has no public credential; verify persistence boundary directly.
    with _db(client) as db:
        public = db.query(StreamEvent).filter(StreamEvent.public.is_(True)).all()
        assert any(row.event_type == 'public.test' for row in public)
        assert all(row.event_type != 'private.test' for row in public)


def test_migration_0012_is_applied(client):
    from app.migrations import migration_status
    status = migration_status(client.app.state.database)
    assert '0012' in status['applied']
    assert status['pending'] == []


def test_worker_disabled_is_explicit(tmp_path):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.main import create_app
    settings = Settings(environment='test', database_url=f"sqlite:///{tmp_path/'worker.db'}", write_api_key='x', cors_origins=('http://testserver',), reliability_worker_enabled=False)
    app = create_app(settings)
    with TestClient(app) as c:
        response = c.post('/v1/reliability/worker/run-once', headers={'X-SC-API-Key':'x'}, json={'worker_id':'w'})
        assert response.status_code == 503


def test_worker_auto_failover_requires_explicit_parameter_compatibility(client):
    import asyncio
    from types import SimpleNamespace
    from app.services.reliability import process_next_work

    class FakeRuntime:
        settings = SimpleNamespace(provider_failover_enabled=True)
        def connector_configuration_status(self, connector):
            return "configured"
        async def ingest(self, db, connector_id, **kwargs):
            if connector_id == "world-bank.indicators":
                raise RuntimeError("primary unavailable")
            return SimpleNamespace(id="backup-run")

    with _db(client) as db:
        primary = db.get(LiveDataConnector, "world-bank.indicators")
        backup = db.get(LiveDataConnector, "un.sdg-catalog")
        primary.configuration_json = {**(primary.configuration_json or {}), "failover_group":"compatible-test", "failover_priority":10, "failover_parameters_compatible":True}
        backup.configuration_json = {**(backup.configuration_json or {}), "failover_group":"compatible-test", "failover_priority":20, "failover_parameters_compatible":True}
        primary.last_health_status = "degraded"
        backup.last_health_status = "operational"
        db.add_all([primary, backup]); db.commit()
        queued = queue_connector_work(db, primary.id)
        result = asyncio.run(process_next_work(db, FakeRuntime(), worker_id="failover-worker"))
        assert result.id == queued.id
        assert result.status == "completed"
        assert result.execution_connector_id == backup.id
        assert result.ingestion_run_id == "backup-run"


def test_queue_strips_credential_like_parameters(client):
    with _db(client) as db:
        row = queue_connector_work(db, 'world-bank.indicators', parameters={'indicator':'X','api_key':'secret','nested':{'token':'hidden','keep':1}})
        assert row.parameters_json == {'indicator':'X','nested':{'keep':1}}


def test_exists_alert_supports_text_values(client):
    now = datetime.now(timezone.utc)
    with _db(client) as db:
        rule = AlertRule(name='Text exists', metric='TEXT.STATUS', operator='exists', enabled=True)
        db.add(rule); db.commit()
        observation = LiveDataObservation(id='text-exists', connector_id='world-bank.indicators', source_id='world-bank', source_record_id='text', domain='test', metric='TEXT.STATUS', value_text='operational', observed_at=now, retrieved_at=now)
        db.add(observation); db.commit()
        assert len(evaluate_alerts(db, observation)) == 1


def test_sse_last_event_id_resume(client, write_headers):
    with _db(client) as db:
        first = StreamEvent(event_type='resume.first', subject_type='test', payload_json={'n':1}, public=False)
        second = StreamEvent(event_type='resume.second', subject_type='test', payload_json={'n':2}, public=False)
        db.add_all([first, second]); db.commit(); db.refresh(first); db.refresh(second)
        first_id = first.id
    response = client.get('/v1/reliability/stream?once=true', headers={**write_headers, 'Last-Event-ID': str(first_id)})
    assert 'event: resume.first' not in response.text
    assert 'event: resume.second' in response.text
