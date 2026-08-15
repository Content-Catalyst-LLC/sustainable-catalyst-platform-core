from dataclasses import replace
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from sqlalchemy import update
from app.config import Settings
from app.main import create_app
from app.models import ChangeControlRecord, OperationsIncidentEvent
from app.services import observability, operations

def app_client(td, **kwargs):
    s=replace(Settings(),database_url=f"sqlite:///{td}/core.db",observability_request_metrics_enabled=False,**kwargs)
    app=create_app(s); return app,TestClient(app)

def test_readiness_and_migration_0022():
    with TemporaryDirectory() as td:
        app,c=app_client(td); b=c.get('/v1/operations/readiness').json(); assert b['release']=='2.19.0' and b['migration_0022_applied'] and b['automatic_rollback_enabled'] is False

def test_incident_idempotency_and_non_public_visibility():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            a=operations.create_incident(db,title='x',severity='sev2',idempotency_key='same'); b=operations.create_incident(db,title='other',severity='sev2',idempotency_key='same'); assert a.id==b.id
            try: operations.create_incident(db,title='public',visibility='public')
            except ValueError: pass
            else: raise AssertionError('public incident accepted')

def test_invalid_severity_is_rejected():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            try: operations.create_incident(db,title='x',severity='catastrophic')
            except ValueError: pass
            else: raise AssertionError('invalid severity accepted')

def test_incident_transition_and_hash_chain_verification():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            row=operations.create_incident(db,title='x',severity='sev2'); operations.append_event(db,row,event_type='incident.state_changed',new_state='investigating',actor='ops'); operations.append_event(db,row,event_type='incident.state_changed',new_state='mitigated',actor='ops'); assert operations.verify_event_chain(db,row.id)['valid'] is True

def test_incident_event_tamper_is_detected():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            row=operations.create_incident(db,title='x'); event=operations.events(db,row.id)[0]; db.execute(update(OperationsIncidentEvent).where(OperationsIncidentEvent.id==event.id).values(note='tampered')); db.commit(); assert operations.verify_event_chain(db,row.id)['valid'] is False

def test_high_risk_change_requires_approval_before_start():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            row=operations.create_change(db,app.state.settings,change_key='high-1',risk='high',release='2.19.0'); assert row.approval_required
            try: operations.start_change(db,row,actor='ops')
            except ValueError: pass
            else: raise AssertionError('unapproved high-risk change started')
            operations.approve_change(db,row,actor='reviewer'); operations.start_change(db,row,actor='ops'); assert row.state=='in_progress'

def test_low_risk_change_can_start_without_approval():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            row=operations.create_change(db,app.state.settings,change_key='low-1',risk='low'); operations.start_change(db,row,actor='ops'); assert row.state=='in_progress' and not row.approval_required

def test_rollback_recommendation_is_correlation_only_and_operator_confirmed():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            inc=operations.create_incident(db,title='outage',severity='sev1'); dep=observability.create_deployment_marker(db,release='2.19.0',environment='production',state='deployed'); rb=operations.assess_rollback(db,incident=inc,deployment_marker_id=dep.id,slo_evaluations=[{'name':'availability','state':'breached'}]); assert rb.recommendation=='recommended' and rb.automatic_execution is False and rb.causal_attribution is False
            try: operations.decide_rollback(db,rb,state='executed',actor='ops')
            except ValueError: pass
            else: raise AssertionError('rollback executed without acknowledgement')
            operations.decide_rollback(db,rb,state='acknowledged',actor='ops'); operations.decide_rollback(db,rb,state='executed',actor='ops'); assert rb.state=='executed' and rb.automatic_execution is False

def test_no_breach_does_not_auto_recommend_rollback():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            inc=operations.create_incident(db,title='issue',severity='sev2'); dep=observability.create_deployment_marker(db,release='2.19.0',environment='production',state='deployed'); rb=operations.assess_rollback(db,incident=inc,deployment_marker_id=dep.id,slo_evaluations=[{'state':'met'}]); assert rb.recommendation=='review'

def test_secret_fields_are_redacted_from_incident_and_change_metadata():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db:
            inc=operations.create_incident(db,title='x',metadata={'token':'hide','safe':'keep'}); ch=operations.create_change(db,app.state.settings,change_key='s',details={'password':'hide','safe':'keep'}); assert 'token' not in inc.metadata_json and inc.metadata_json['safe']=='keep'; assert 'password' not in ch.details_json

def test_public_status_is_aggregate_only():
    with TemporaryDirectory() as td:
        app,c=app_client(td)
        with app.state.database.session_factory() as db: operations.create_incident(db,title='sensitive title',severity='sev2')
        r=c.get('/api/v1/operations/status'); assert r.status_code in (200,401,403)
        if r.status_code==200:
            data=r.json()['data']; assert data['open_incidents']==1 and data['incident_details_publicly_exposed'] is False and 'items' not in data

def test_internal_api_round_trip():
    with TemporaryDirectory() as td:
        app,c=app_client(td); r=c.post('/v1/operations/incidents',json={'title':'API incident','severity':'sev3','idempotency_key':'api-1'}); assert r.status_code==200; iid=r.json()['id']; assert c.post(f'/v1/operations/incidents/{iid}/transition',json={'state':'investigating','actor':'ops'}).status_code==200; v=c.get(f'/v1/operations/incidents/{iid}/events/verify'); assert v.status_code==200 and v.json()['valid'] is True
