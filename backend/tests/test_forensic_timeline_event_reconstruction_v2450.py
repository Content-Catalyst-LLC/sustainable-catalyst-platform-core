from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2450.db'}",version='2.52.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:timeline-v2450',entity_type='research-project',slug='timeline-v2450',name='Timeline v2450',visibility='public')); db.commit()


def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:timeline-v2450','investigation_key':'case-245','name':'Case 245','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'ev-1','evidence_kind':'record','label':'Timestamp record','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    obj=c.post(f'/v1/open-forensics/investigations/{iid}/objects',json={'data':{'object_key':'person-ref','object_kind':'statement','label':'Participant reference'}}); assert obj.status_code==200,obj.text
    return iid,ev.json()['id'],obj.json()['id']


def test_v2450_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.52.0' and h['open_forensics'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.52.0' and r['migration_0049_applied'] is True
    for key in ('forensic_event_registry_by_core','bounded_temporal_assertion_capture_by_core','event_evidence_binding_by_core','explicit_event_relation_registry_by_core','reconstruction_hypothesis_registry_by_core','renderer_neutral_timeline_specification_by_core','immutable_timeline_snapshots_by_core'):
        assert r[key] is True,key
    for key in ('automatic_event_inference_by_core','automatic_timestamp_inference_by_core','automatic_sequence_truth_determination_by_core','automatic_participant_identity_resolution_by_core','automatic_truth_promotion'):
        assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_events_bindings_participants_relations_and_timeline(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,evidence_id,object_id=case(c)
    a=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'e1','label':'First observation','event_kind':'observation','temporal_basis':'observed','time_precision':'minute','start_time':'2026-09-13T10:00:00Z'}}); assert a.status_code==200,a.text
    b=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'e2','label':'Later communication','event_kind':'communication','temporal_basis':'asserted','time_precision':'bounded','earliest_time':'2026-09-13T10:10:00Z','latest_time':'2026-09-13T10:30:00Z'}}); assert b.status_code==200,b.text
    bind=c.post(f"/v1/open-forensics/investigations/{iid}/events/{a.json()['id']}/evidence-bindings",json={'data':{'binding_key':'e1-time','evidence_item_id':evidence_id,'role':'supports-time','temporal_assertion':{'field':'start_time'}}}); assert bind.status_code==200,bind.text
    participant=c.post(f"/v1/open-forensics/investigations/{iid}/events/{b.json()['id']}/participants",json={'data':{'participant_key':'p1','forensic_object_id':object_id,'role':'referenced','basis_evidence_item_id':evidence_id}}); assert participant.status_code==200,participant.text
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/event-relations',json={'data':{'relation_key':'e1-before-e2','source_event_id':a.json()['id'],'target_event_id':b.json()['id'],'relation_kind':'before','basis_evidence_ids':[evidence_id]}}); assert rel.status_code==200,rel.text
    timeline=c.get(f'/v1/open-forensics/investigations/{iid}/timeline').json(); assert len(timeline['events'])==2 and len(timeline['relations'])==1 and len(timeline['evidence_bindings'])==1 and len(timeline['participants'])==1
    assert timeline['reconstructed_sequence_is_hypothesis'] is True and 'not-sequence-truth' in timeline['ordering_method']
    spec=c.get(f'/v1/open-forensics/investigations/{iid}/timeline-specification').json(); assert spec['visual_kind']=='forensic-timeline' and spec['renderer_neutral'] is True and spec['execution']['automatic_sequence_truth_determination'] is False


def test_reconstruction_hypothesis_views_and_immutable_snapshots(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,evidence_id,_=case(c)
    claim=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'focal','statement':'The event sequence is disputed.'}}); assert claim.status_code==200,claim.text
    hyp=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'sequence-a','label':'Sequence A','statement':'Observation preceded communication.','focal_claim_id':claim.json()['id']}}); assert hyp.status_code==200,hyp.text
    e1=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'a','label':'A','event_kind':'observation','start_time':'2026-09-13T10:00:00Z','time_precision':'minute'}}).json()
    e2=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'b','label':'B','event_kind':'communication','start_time':'2026-09-13T10:20:00Z','time_precision':'minute'}}).json()
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/event-relations',json={'data':{'relation_key':'a-b','source_event_id':e1['id'],'target_event_id':e2['id'],'relation_kind':'before','basis_evidence_ids':[evidence_id]}}).json()
    rec=c.post(f'/v1/open-forensics/investigations/{iid}/event-reconstructions',json={'data':{'reconstruction_key':'r1','label':'Working reconstruction','hypothesis_id':hyp.json()['id'],'ordered_event_ids':[e1['id'],e2['id']],'event_relation_ids':[rel['id']],'assumptions':['record timestamps are comparable'],'unresolved_conflicts':['participant timing not independently verified']}}); assert rec.status_code==200,rec.text
    view=c.post(f'/v1/open-forensics/investigations/{iid}/timeline-views',json={'data':{'view_key':'main','label':'Main timeline','event_ids':[e1['id'],e2['id']],'reconstruction_ids':[rec.json()['id']]}}); assert view.status_code==200,view.text
    snap1=c.post(f'/v1/open-forensics/investigations/{iid}/timeline-snapshots',json={'data':{'created_by':'test'}}); assert snap1.status_code==200 and snap1.json()['revision']==1 and len(snap1.json()['content_hash'])==64
    snap2=c.post(f'/v1/open-forensics/investigations/{iid}/timeline-snapshots',json={'data':{'created_by':'test'}}); assert snap2.status_code==200 and snap2.json()['revision']==2 and snap2.json()['previous_snapshot_hash']==snap1.json()['content_hash']
    timeline=c.get(f'/v1/open-forensics/investigations/{iid}/timeline').json(); assert len(timeline['reconstructions'])==1 and len(timeline['views'])==1


def test_v2450_rejects_sequence_truth_probability_and_invalid_temporal_state(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,_,_=case(c)
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'bad-time','label':'Bad','start_time':'2026-09-13T11:00:00Z','end_time':'2026-09-13T10:00:00Z'}}); assert bad.status_code==422
    e1=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'a','label':'A'}}).json(); e2=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'b','label':'B'}}).json()
    bad_rec=c.post(f'/v1/open-forensics/investigations/{iid}/event-reconstructions',json={'data':{'reconstruction_key':'bad','label':'Bad reconstruction','ordered_event_ids':[e1['id'],e2['id']],'confirmed_sequence':True}}); assert bad_rec.status_code==422 and 'sequence truth' in bad_rec.text
    same=c.post(f'/v1/open-forensics/investigations/{iid}/event-relations',json={'data':{'relation_key':'same','source_event_id':e1['id'],'target_event_id':e1['id'],'relation_kind':'before'}}); assert same.status_code==422
