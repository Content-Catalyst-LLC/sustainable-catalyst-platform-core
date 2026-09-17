#!/usr/bin/env python3
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity
with tempfile.TemporaryDirectory() as td:
    app=create_app(Settings(database_url=f"sqlite:///{Path(td)/'v2470-smoke.db'}",version='2.47.0')); c=TestClient(app)
    with app.state.database.session_factory() as db: db.add(Entity(id='project:v247-smoke',entity_type='research-project',slug='v247-smoke',name='v247 smoke',visibility='public')); db.commit()
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:v247-smoke','investigation_key':'smoke','name':'Smoke','visibility':'public'}}).json(); iid=inv['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'img','evidence_kind':'media','label':'Image','content_hash':'a'*64}}).json()
    a1=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'orig','label':'Original','media_kind':'image','provenance_role':'original','evidence_item_id':ev['id'],'content_hash':'a'*64}}).json(); a2=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'copy','label':'Copy','media_kind':'image','provenance_role':'derivative','source_ref':'external:copy'}}).json()
    c.post(f'/v1/open-forensics/investigations/{iid}/media-derivations',json={'data':{'derivation_key':'d','parent_artifact_id':a1['id'],'child_artifact_id':a2['id'],'transformation_kind':'re-encode'}}).raise_for_status(); c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts/{a1["id"]}/fingerprints',json={'data':{'fingerprint_key':'sha','fingerprint_kind':'cryptographic','algorithm':'sha256','fingerprint_value':'a'*64}}).raise_for_status(); c.post(f'/v1/open-forensics/investigations/{iid}/media-provenance-snapshots',json={'data':{'created_by':'smoke'}}).raise_for_status()
    graph=c.get(f'/v1/open-forensics/investigations/{iid}/media-lineage-graph').json(); ready=c.get('/v1/open-forensics/readiness').json(); status=migration_status(app.state.database); assert len(graph['nodes'])==2 and len(graph['edges'])==1; assert ready['migration_0051_applied'] is True and ready['derivative_detection_by_core'] is False and ready['authenticity_determination_from_media_by_core'] is False; assert status['pending']==[]; print('PASS - Platform Core v2.47.0 Media Artifact & Derivative Provenance runtime validation')
