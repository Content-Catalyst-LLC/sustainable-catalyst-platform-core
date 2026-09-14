from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2460.db'}",version='2.47.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:forensic-spacetime-v2460',entity_type='research-project',slug='forensic-spacetime-v2460',name='Forensic Space Time v2460',visibility='public'))
        db.commit()


def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:forensic-spacetime-v2460','investigation_key':'case-246','name':'Case 246','visibility':'public'}})
    assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'gps-log','evidence_kind':'digital','label':'GPS log','content_hash':'a'*64}})
    assert ev.status_code==200,ev.text
    event=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'arrival','label':'Arrival','event_kind':'movement','temporal_basis':'observed','start_time':'2026-09-13T10:00:00Z','time_precision':'minute'}})
    assert event.status_code==200,event.text
    return iid,ev.json()['id'],event.json()['id']


def test_v2460_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.47.0' and h['open_forensics'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.47.0' and r['migration_0050_applied'] is True
    for key in ('forensic_place_registry_by_core','evidence_spatial_binding_by_core','event_place_binding_by_core','spatial_uncertainty_envelopes_by_core','trajectory_evidence_registry_by_core','explicit_spatial_temporal_intersections_by_core','linked_map_timeline_specification_by_core','site_intelligence_handoffs_by_core','immutable_spatial_temporal_snapshots_by_core'):
        assert r[key] is True,key
    for key in ('crs_reprojection_by_core','spatial_join_by_core','routing_by_core','remote_sensing_by_core','trajectory_interpolation_execution_by_core','automatic_location_truth_determination_by_core','automatic_truth_promotion'):
        assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_places_evidence_event_bindings_scene_and_handoff(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,evidence_id,event_id=case(c)
    place=c.post(f'/v1/open-forensics/investigations/{iid}/places',json={'data':{'place_key':'station','label':'Station','place_kind':'facility','geometry':{'type':'Point','coordinates':[-90.2,38.6]},'site_intelligence_ref':'site-intelligence:feature:station'}})
    assert place.status_code==200,place.text; pid=place.json()['id']
    eb=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{evidence_id}/spatial-bindings',json={'data':{'binding_key':'gps-station','place_id':pid,'spatial_role':'supports-location','site_intelligence_ref':'site-intelligence:record:gps'}})
    assert eb.status_code==200,eb.text
    ep=c.post(f'/v1/open-forensics/investigations/{iid}/events/{event_id}/place-bindings',json={'data':{'binding_key':'arrival-station','place_id':pid,'role':'occurred-at','basis_evidence_ids':[evidence_id]}})
    assert ep.status_code==200,ep.text
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-evidence').json()
    assert len(bundle['places'])==1 and len(bundle['evidence_spatial_bindings'])==1 and len(bundle['event_place_bindings'])==1
    assert bundle['spatial_relations_are_explicit_assertions_not_computed_truth'] is True
    spec=c.get(f'/v1/open-forensics/investigations/{iid}/forensic-scene-specification').json()
    assert spec['visual_kind']=='forensic-linked-map-timeline' and spec['renderer_neutral'] is True
    assert spec['execution']['spatial_join_by_core'] is False and spec['execution']['remote_sensing_by_core'] is False
    handoff=c.get(f'/v1/open-forensics/investigations/{iid}/site-intelligence-handoff').json()
    assert handoff['target_product']=='site-intelligence' and handoff['reference_first'] is True and handoff['execution_by_core'] is False
    assert 'site-intelligence:feature:station' in handoff['site_intelligence_refs']


def test_uncertainty_trajectory_intersection_view_and_snapshot(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,evidence_id,event_id=case(c)
    place=c.post(f'/v1/open-forensics/investigations/{iid}/places',json={'data':{'place_key':'zone','label':'Search zone','geometry':{'type':'Polygon','coordinates':[[[-90.3,38.5],[-90.1,38.5],[-90.1,38.7],[-90.3,38.7],[-90.3,38.5]]]}}}).json()
    env=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-uncertainty-envelopes',json={'data':{'envelope_key':'arrival-zone','subject_kind':'event','subject_ref':event_id,'uncertainty_kind':'bounded-region','geometry':{'type':'Polygon','coordinates':[[[-90.25,38.55],[-90.15,38.55],[-90.15,38.65],[-90.25,38.65],[-90.25,38.55]]]},'basis_evidence_ids':[evidence_id],'coverage_label':'location uncertainty'}})
    assert env.status_code==200,env.text
    traj=c.post(f'/v1/open-forensics/investigations/{iid}/trajectory-evidence',json={'data':{'trajectory_key':'gps-path','label':'Observed GPS path','subject_ref':'forensic-object:vehicle','basis_evidence_ids':[evidence_id],'site_intelligence_ref':'site-intelligence:trajectory:gps','ordered_points':[{'observed_at':'2026-09-13T09:55:00Z','geometry':{'type':'Point','coordinates':[-90.25,38.58]}},{'observed_at':'2026-09-13T10:00:00Z','geometry':{'type':'Point','coordinates':[-90.2,38.6]}}]}})
    assert traj.status_code==200,traj.text; tid=traj.json()['id']
    inter=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-intersections',json={'data':{'intersection_key':'arrival-zone-match','event_id':event_id,'place_id':place['id'],'trajectory_id':tid,'relation_kind':'asserted','basis_evidence_ids':[evidence_id],'temporal_window':{'start':'2026-09-13T09:55:00Z','end':'2026-09-13T10:05:00Z'}}})
    assert inter.status_code==200,inter.text
    view=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-views',json={'data':{'view_key':'linked','label':'Linked map and timeline','event_ids':[event_id],'place_ids':[place['id']],'trajectory_ids':[tid],'display':{'kind':'linked-map-timeline'}}})
    assert view.status_code==200,view.text
    s1=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-snapshots',json={'data':{'created_by':'test'}}); assert s1.status_code==200 and s1.json()['revision']==1 and len(s1.json()['content_hash'])==64
    s2=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-snapshots',json={'data':{'created_by':'test'}}); assert s2.status_code==200 and s2.json()['revision']==2 and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']


def test_v2460_rejects_computed_truth_and_bad_trajectory(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,evidence_id,event_id=case(c)
    bad_place=c.post(f'/v1/open-forensics/investigations/{iid}/places',json={'data':{'place_key':'bad','label':'Bad','geometry':{'type':'Point','coordinates':[0,0]},'confirmed_location':True}})
    assert bad_place.status_code==422 and 'does not determine' in bad_place.text
    bad_traj=c.post(f'/v1/open-forensics/investigations/{iid}/trajectory-evidence',json={'data':{'trajectory_key':'bad-path','label':'Bad path','subject_ref':'x','basis_evidence_ids':[evidence_id],'ordered_points':[{'observed_at':'2026-09-13T10:05:00Z','geometry':{'type':'Point','coordinates':[0,0]}},{'observed_at':'2026-09-13T10:00:00Z','geometry':{'type':'Point','coordinates':[1,1]}}]}})
    assert bad_traj.status_code==422 and 'time ordered' in bad_traj.text
    bad_geom=c.post(f'/v1/open-forensics/investigations/{iid}/spatial-uncertainty-envelopes',json={'data':{'envelope_key':'bad-geom','subject_kind':'event','subject_ref':event_id,'geometry':{'type':'Raster','coordinates':[]}}})
    assert bad_geom.status_code==422


def test_public_spatial_temporal_evidence_for_public_case(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,_,_=case(c)
    r=c.get(f'/api/v1/open-forensics/investigations/{iid}/spatial-temporal-evidence')
    assert r.status_code==401 and 'public API key is required' in r.text
