#!/usr/bin/env python3
import tempfile
from pathlib import Path
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import Entity
from app.services import predictive_intelligence as p
with tempfile.TemporaryDirectory() as td:
 db=Database(f"sqlite:///{Path(td)/'v2520.db'}"); run_migrations(db)
 with db.session_factory() as s:
  s.add(Entity(id='project:smoke-v2520',entity_type='research-project',slug='smoke-v2520',name='Predictive Smoke')); s.commit()
  m=p.create_model(s,{'project_entity_id':'project:smoke-v2520','model_key':'m','name':'Forecast','runtime_product':'lab'})
  t=p.add_target(s,m['id'],{'target_key':'y','label':'Y','unit':'unit'}); p.add_feature(s,m['id'],{'feature_key':'x','label':'X','source_product':'catalyst-data','source_ref':'catalyst-data://x'})
  w=p.add_training_window(s,m['id'],{'window_key':'w','dataset_ref':'catalyst-data://train'})
  r=p.add_forecast_run(s,m['id'],{'run_key':'r','training_window_id':w['id'],'runtime_product':'lab'}); p.add_forecast_observation(s,m['id'],r['id'],{'target_id':t['id'],'forecast_value':1.0}); p.add_handoff(s,m['id'],{'handoff_key':'h','target_product':'lab'}); snap=p.create_snapshot(s,m['id'],{})
  ready=p.readiness(s); status=migration_status(db); print({'version':'2.52.0','migration_0056_applied':ready['migration_0056_applied'],'models':ready['counts']['models'],'forecast_inference_execution_by_core':ready['forecast_inference_execution_by_core'],'automatic_truth_promotion':ready['automatic_truth_promotion'],'snapshot_hash_len':len(snap['content_hash']),'pending':status['pending']})
  assert ready['migration_0056_applied'] and ready['forecast_inference_execution_by_core'] is False and ready['automatic_truth_promotion'] is False and len(snap['content_hash'])==64 and status['pending']==[]
print('PASS - Platform Core v2.52.0 Predictive Model Object Model & Forecast Provenance runtime validation')
