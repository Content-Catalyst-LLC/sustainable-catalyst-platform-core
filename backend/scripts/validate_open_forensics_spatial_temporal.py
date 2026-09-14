#!/usr/bin/env python3
import os
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity

app=create_app(Settings(database_url=os.getenv("SC_CORE_DATABASE_URL","sqlite:///./platform_core.db"),version="2.46.0"))
c=TestClient(app)
with app.state.database.session_factory() as db:
    if db.get(Entity,'project:v2460-smoke') is None:
        db.add(Entity(id='project:v2460-smoke',entity_type='research-project',slug='v2460-smoke',name='v2460 smoke',visibility='public')); db.commit()
inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:v2460-smoke','investigation_key':'smoke-2460','name':'v2460 smoke','visibility':'public'}})
assert inv.status_code in (200,409),inv.text
if inv.status_code==200: iid=inv.json()['id']
else:
    items=c.get('/v1/open-forensics/investigations').json(); iid=next(x['id'] for x in items if x['investigation_key']=='smoke-2460')
ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'gps','evidence_kind':'digital','label':'GPS','content_hash':'b'*64}})
if ev.status_code==200: eid=ev.json()['id']
else: eid=c.get(f'/v1/open-forensics/investigations/{iid}/bundle').json()['evidence_items'][0]['id']
event=c.post(f'/v1/open-forensics/investigations/{iid}/events',json={'data':{'event_key':'arrive','label':'Arrive','event_kind':'movement','start_time':'2026-09-13T10:00:00Z','time_precision':'minute'}})
if event.status_code==200: event_id=event.json()['id']
else: event_id=c.get(f'/v1/open-forensics/investigations/{iid}/timeline').json()['events'][0]['id']
place=c.post(f'/v1/open-forensics/investigations/{iid}/places',json={'data':{'place_key':'p1','label':'Place 1','geometry':{'type':'Point','coordinates':[-90.2,38.6]},'site_intelligence_ref':'site-intelligence:feature:p1'}})
assert place.status_code in (200,409),place.text
if place.status_code==200: pid=place.json()['id']
else: pid=c.get(f'/v1/open-forensics/investigations/{iid}/spatial-temporal-evidence').json()['places'][0]['id']
b=c.post(f'/v1/open-forensics/investigations/{iid}/evidence/{eid}/spatial-bindings',json={'data':{'binding_key':'gps-p1','place_id':pid,'spatial_role':'supports-location'}}); assert b.status_code in (200,409),b.text
bp=c.post(f'/v1/open-forensics/investigations/{iid}/events/{event_id}/place-bindings',json={'data':{'binding_key':'event-p1','place_id':pid,'role':'occurred-at','basis_evidence_ids':[eid]}}); assert bp.status_code in (200,409),bp.text
spec=c.get(f'/v1/open-forensics/investigations/{iid}/forensic-scene-specification').json(); assert spec['visual_kind']=='forensic-linked-map-timeline' and spec['execution']['spatial_join_by_core'] is False
r=c.get('/v1/open-forensics/readiness').json(); assert r['migration_0050_applied'] is True and r['automatic_location_truth_determination_by_core'] is False
print({'version':c.get('/health').json()['version'],'migration_0050_applied':r['migration_0050_applied'],'places':r['counts']['places'],'spatial_join_by_core':r['spatial_join_by_core'],'automatic_location_truth_determination_by_core':r['automatic_location_truth_determination_by_core']})
print('PASS - Platform Core v2.46.0 Forensic Spatial/Temporal Evidence Integration runtime validation')
