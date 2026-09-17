#!/usr/bin/env python3
from app.migrations import migration_status
from app.models import Entity, CausalGraphRecord, CausalVariableRecord
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
import os,tempfile
fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
try:
 app=create_app(Settings(database_url='sqlite:///'+p,version='2.58.0')); c=TestClient(app)
 with app.state.database.session_factory() as db:
  db.add(Entity(id='project:v2580-validator',entity_type='research-project',slug='v2580-validator',name='v2580 validator',visibility='public'))
  db.add(CausalGraphRecord(id='graph:v2580-validator',graph_key='validator-dag',name='Validator DAG',project_entity_id='project:v2580-validator',visibility='public')); db.flush()
  db.add(CausalVariableRecord(id='variable:v2580-validator',graph_id='graph:v2580-validator',variable_key='outcome',label='Outcome',causal_role='outcome')); db.commit()
 d=c.get('/v1/predictive-intelligence/readiness').json(); assert d['release']=='2.58.0' and d['migration_0062_applied'] is True
 for k in ('causal_predictive_study_registry_by_core','causal_variable_binding_registry_by_core','intervention_scenario_registry_by_core','counterfactual_forecast_provenance_by_core','causal_effect_evidence_registry_by_core','causal_predictive_evaluation_evidence_by_core','causal_predictive_handoff_registry_by_core','reproducible_causal_predictive_packages_by_core'): assert d[k] is True,k
 for k in ('causal_structure_learning_by_core','causal_identification_by_core','causal_effect_estimation_by_core','counterfactual_execution_by_core','intervention_simulation_by_core','causal_predictive_metric_computation_by_core','decision_optimization_by_core'): assert d[k] is False,k
 m=migration_status(app.state.database); assert '0062' in m['applied'] and m['pending']==[],m
 print('PASS - Platform Core v2.58.0 causal-predictive integration invariants')
finally:
 try: os.remove(p)
 except OSError: pass
