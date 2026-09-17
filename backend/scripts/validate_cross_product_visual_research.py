#!/usr/bin/env python3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models import Entity

with tempfile.TemporaryDirectory(prefix='sc-core-v2400-') as tmp:
    app=create_app(Settings(database_url=f"sqlite:///{Path(tmp)/'validate.db'}",version='2.40.0'))
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:v2400',entity_type='research-project',slug='v2400',name='v2.40 validation',visibility='public'));db.commit()
    c=TestClient(app)
    h=c.get('/health').json(); assert h['version']=='2.40.0' and h['cross_product_visual_research_objects'] is True
    r=c.get('/v1/cross-product-visual-research/readiness').json(); assert r['migration_0044_applied'] is True and r['reference_first_cross_product'] is True
    created=c.post('/v1/cross-product-visual-research',json={'data':{'project_entity_id':'project:v2400','object_key':'validation','name':'Validation object','visibility':'public'}}); assert created.status_code==200,created.text
    oid=created.json()['id']
    core=c.post(f'/v1/cross-product-visual-research/{oid}/members',json={'data':{'member_key':'core','member_kind':'research-object','source_product':'platform-core','label':'Core project','local_entity_id':'project:v2400'}}); assert core.status_code==200,core.text
    lab=c.post(f'/v1/cross-product-visual-research/{oid}/members',json={'data':{'member_key':'lab','member_kind':'result','source_product':'lab','label':'Lab result','source_ref':{'artifact_id':'lab:test:1'}}}); assert lab.status_code==200,lab.text
    rel=c.post(f'/v1/cross-product-visual-research/{oid}/relations',json={'data':{'relation_key':'informs','source_member_id':core.json()['id'],'target_member_id':lab.json()['id'],'relation_kind':'informs'}}); assert rel.status_code==200,rel.text
    spec=c.get(f'/v1/cross-product-visual-research/{oid}/visualization').json(); assert spec['contract']=='sc.cross-product-visual-research-object.v1' and spec['validation']['cross_product'] is True
    pkg=c.get(f'/v1/cross-product-visual-research/{oid}/portable-package').json(); assert pkg['portable'] is True and pkg['embedded_remote_content'] is False
    assert spec['renderer_execution_by_core'] is False and spec['layout_execution_by_core'] is False
print('PASS - Platform Core v2.40.0 Cross-Product Visual Research Objects runtime validation')
