#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import predictive_intelligence as svc
from app.models import Entity
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
import os,tempfile
fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
try:
 app=create_app(Settings(database_url='sqlite:///'+p,version='2.57.0')); c=TestClient(app)
 with app.state.database.session_factory() as db: db.add(Entity(id='project:v2570-validator',entity_type='research-project',slug='v2570-validator',name='v2570 validator',visibility='public')); db.commit()
 d=c.get('/v1/predictive-intelligence/readiness').json(); assert d['release']=='2.57.0' and d['migration_0061_applied'] is True
 for k in ('spatial_temporal_study_registry_by_core','spatial_unit_registry_by_core','spatial_temporal_forecast_provenance_by_core','spatial_temporal_observation_registry_by_core','propagation_evidence_registry_by_core','hotspot_evidence_registry_by_core','spatial_temporal_evaluation_evidence_by_core','reproducible_spatial_temporal_packages_by_core'): assert d[k] is True,k
 for k in ('spatial_interpolation_by_core','spatial_inference_execution_by_core','trajectory_prediction_by_core','propagation_modeling_by_core','hotspot_detection_by_core','spatial_temporal_metric_computation_by_core'): assert d[k] is False,k
 m=migration_status(app.state.database); assert '0061' in m['applied'] and m['pending']==[],m
 print('PASS - Platform Core v2.57.0 spatial-temporal predictive intelligence invariants')
finally:
 try: os.remove(p)
 except OSError: pass
