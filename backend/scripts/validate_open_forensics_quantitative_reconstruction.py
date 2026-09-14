#!/usr/bin/env python3
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity
with tempfile.TemporaryDirectory() as td:
    app=create_app(Settings(database_url=f"sqlite:///{Path(td)/'v2480-smoke.db'}",version='2.48.0')); c=TestClient(app)
    with app.state.database.session_factory() as db: db.add(Entity(id='project:v248-smoke',entity_type='research-project',slug='v248-smoke',name='v248 smoke',visibility='public')); db.commit()
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:v248-smoke','investigation_key':'smoke','name':'Smoke','visibility':'public'}}).json(); iid=inv['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'m','evidence_kind':'measurement','label':'Measurement','content_hash':'a'*64}}).json()
    rec=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions',json={'data':{'reconstruction_key':'r','label':'R','reconstruction_kind':'physical','preferred_runtime':'workbench','basis_evidence_ids':[ev['id']]}}).json(); rid=rec['id']
    c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/measurements',json={'data':{'measurement_key':'x','label':'X','value':{'value':1.0},'unit':'m','uncertainty':{'lower':0.9,'upper':1.1},'evidence_item_id':ev['id']}}).raise_for_status()
    h=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/handoffs',json={'data':{'handoff_key':'wb','target_product':'workbench'}}).json()
    c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-handoffs/{h["id"]}/results',json={'data':{'result_key':'result','external_result_ref':'sc://workbench/run/1/result','result_kind':'output','content_hash':'b'*64}}).raise_for_status()
    pkg=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/reproduction-packages',json={'data':{'package_key':'pkg'}}).json()
    ready=c.get('/v1/open-forensics/readiness').json(); status=migration_status(app.state.database)
    assert ready['migration_0052_applied'] is True and ready['quantitative_model_execution_by_core'] is False and ready['workbench_lab_handoff_contracts_by_core'] is True
    assert len(pkg['manifest_hash'])==64 and status['pending']==[]
    print('PASS - Platform Core v2.48.0 Quantitative Reconstruction & Reproduction Handoffs runtime validation')
