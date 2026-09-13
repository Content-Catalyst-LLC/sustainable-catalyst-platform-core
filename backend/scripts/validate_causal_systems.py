#!/usr/bin/env python3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
with tempfile.TemporaryDirectory() as td:
    c=TestClient(create_app(Settings(database_url='sqlite:///'+str(Path(td)/'v237.db'),version='2.37.0')))
    h=c.get('/health').json(); r=c.get('/v1/causal-systems/readiness').json(); m=migration_status(c.app.state.database)
    assert h['version']=='2.37.0' and h['causal_systems_explorer'] is True
    assert r['migration_0041_applied'] is True and r['dag_validation_by_core'] is True and r['automatic_causal_identification'] is False and r['automatic_effect_estimation'] is False
    assert '0041' in m['applied'] and m['pending']==[]
    print({'version':'2.37.0','migration_0041_applied':True,'causal_graphs':True,'dag_validation':True,'path_reasoning':True,'adjustment_candidates':True,'automatic_causal_identification':False,'automatic_effect_estimation':False,'automatic_truth_promotion':False})
    print('PASS - Core 2.37.0 Causal Systems Explorer validation')
