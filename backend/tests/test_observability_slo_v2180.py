from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.main import create_app
from app.models import ObservabilityMetricSample
from app.services import observability


def app_client(tmp, **kw):
    settings=Settings(database_url='sqlite:///'+str(Path(tmp)/'core.db'), **kw)
    app=create_app(settings); return app,TestClient(app)

def test_health_and_readiness_expose_observability():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        assert c.get('/health').json()['version']=='2.25.0'
        assert c.get('/health').json()['observability_slo_production_operations'] is True
        r=c.get('/v1/observability/readiness'); assert r.status_code==200
        b=r.json(); assert b['release']=='2.25.0' and b['migration_0021_applied'] is True and b['external_monitoring_provider_required'] is False

def test_request_metrics_are_recorded_without_query_strings():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        assert c.get('/health?secret=do-not-store').status_code==200
        with app.state.database.session_factory() as db:
            rows=db.scalars(select(ObservabilityMetricSample).where(ObservabilityMetricSample.route=='/health')).all()
            assert rows and all('secret' not in (r.route or '') for r in rows)

def test_summary_calculates_availability_error_rate_and_p95():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            for code,ms in [(200,10),(200,20),(200,30),(500,200)]: observability.record_request(db,method='GET',route='/x',status_code=code,duration_ms=ms)
            s=observability.summary(db,'platform-core',60)
            assert s['sample_count']==4 and s['availability_percent']==75.0 and s['error_rate_percent']==25.0 and s['latency_p95_ms']==200.0

def test_slo_evaluation_met_breached_and_insufficient_data():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            # seeded SLOs require 5 samples; custom ones exercise all states
            a=observability.create_slo(db,service='svc',name='avail',indicator='availability_percent',target=90,window_minutes=60,minimum_samples=2)
            l=observability.create_slo(db,service='svc',name='latency',indicator='latency_p95_ms',target=50,window_minutes=60,minimum_samples=2)
            i=observability.create_slo(db,service='empty',name='empty',indicator='availability_percent',target=99,minimum_samples=2)
            observability.record_request(db,service='svc',method='GET',route='/a',status_code=200,duration_ms=10)
            observability.record_request(db,service='svc',method='GET',route='/a',status_code=200,duration_ms=100)
            assert observability.evaluate_slo(db,a)['state']=='met'
            assert observability.evaluate_slo(db,l)['state']=='breached'
            assert observability.evaluate_slo(db,i)['state']=='insufficient_data'

def test_duplicate_slo_is_rejected():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            observability.create_slo(db,service='svc',name='same',indicator='availability_percent',target=99)
            try: observability.create_slo(db,service='svc',name='same',indicator='availability_percent',target=99)
            except ValueError: pass
            else: raise AssertionError('duplicate SLO accepted')

def test_deployment_markers_preserve_release_history():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            observability.create_deployment_marker(db,release='2.25.0',environment='test',state='started',commit_sha='abc')
            observability.create_deployment_marker(db,release='2.25.0',environment='test',state='deployed',commit_sha='def')
            rows=observability.list_deployments(db); assert len(rows)==2 and rows[0].state=='deployed' and rows[1].state=='started'

def test_invalid_deployment_state_is_rejected():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            try: observability.create_deployment_marker(db,release='2.25.0',environment='test',state='magic')
            except ValueError: pass
            else: raise AssertionError('invalid state accepted')

def test_retention_compacts_old_metric_samples():
    from datetime import datetime,timezone,timedelta
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        with app.state.database.session_factory() as db:
            observability.record_metric(db,metric_name='old',value=1,observed_at=datetime.now(timezone.utc)-timedelta(hours=800))
            assert observability.compact_metrics(db,720)==1

def test_public_status_is_aggregate_only():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        r=c.get('/api/v1/observability/status')
        assert r.status_code in (200,401,403)
        if r.status_code==200:
            data=r.json()['data']; assert data['request_ids_publicly_exposed'] is False and data['operator_metadata_publicly_exposed'] is False

def test_manual_metric_and_slo_api_round_trip():
    with TemporaryDirectory() as td:
        app,c=app_client(td, observability_request_metrics_enabled=False)
        assert c.post('/v1/observability/metrics',json={'metric_name':'custom.metric','value':3,'unit':'count'}).status_code==200
        r=c.post('/v1/observability/slos',json={'service':'custom','name':'error budget','indicator':'error_rate_percent','target':5,'window_minutes':60,'minimum_samples':1}); assert r.status_code==200
        assert any(x['name']=='error budget' for x in c.get('/v1/observability/slos?service=custom').json()['items'])
