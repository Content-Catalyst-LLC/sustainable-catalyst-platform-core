#!/usr/bin/env python3
import tempfile
from pathlib import Path
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.models import Entity
from app.services import predictive_intelligence as p
with tempfile.TemporaryDirectory() as td:
 db=Database(f"sqlite:///{Path(td)/'v2530.db'}"); run_migrations(db)
 with db.session_factory() as s:
  s.add(Entity(id='project:smoke-v2530',entity_type='research-project',slug='smoke-v2530',name='Backtest Smoke')); s.commit()
  m=p.create_model(s,{'project_entity_id':'project:smoke-v2530','model_key':'m','name':'Forecast','runtime_product':'lab'})
  t=p.add_target(s,m['id'],{'target_key':'y','label':'Y','unit':'unit'})
  d=p.add_time_series_dataset(s,m['id'],{'dataset_key':'d','source_product':'catalyst-data','source_ref':'catalyst-data://series','time_field':'ts','frequency':'1h','manifest_hash':'a'*64})
  b=p.add_baseline_model(s,m['id'],{'baseline_key':'naive','baseline_kind':'naive','runtime_product':'lab'})
  plan=p.create_backtest_plan(s,m['id'],{'plan_key':'p','dataset_id':d['id'],'target_id':t['id'],'strategy':'rolling','baseline_ids':[b['id']],'runtime_product':'lab'})
  fold=p.add_backtest_fold(s,m['id'],plan['id'],{'fold_key':'f0','fold_index':0,'train_end':'2025-01-01T00:00:00+00:00','cutoff_time':'2025-01-01T00:00:00+00:00','test_start':'2025-01-01T01:00:00+00:00','test_end':'2025-01-02T00:00:00+00:00','input_manifest_hash':'b'*64})
  p.add_backtest_observation(s,m['id'],plan['id'],fold['id'],{'target_id':t['id'],'prediction':10.0,'actual':11.0,'actual_source_ref':'catalyst-data://actual'})
  p.add_backtest_evaluation(s,m['id'],plan['id'],{'evaluation_key':'mae','metric_name':'MAE','metric_value':1.0,'evidence_ref':'lab://eval/mae'})
  pkg=p.create_backtest_package(s,m['id'],plan['id'],{'environment':{'runtime':'lab'}})
  ready=p.readiness(s); status=migration_status(db)
  print({'version':'2.53.0','migration_0057_applied':ready['migration_0057_applied'],'backtest_plans':ready['counts']['backtest_plans'],'temporal_leakage_guardrails_by_core':ready['temporal_leakage_guardrails_by_core'],'backtest_execution_by_core':ready['backtest_execution_by_core'],'metric_computation_by_core':ready['metric_computation_by_core'],'package_hash_len':len(pkg['content_hash']),'pending':status['pending']})
  assert ready['migration_0057_applied'] and ready['temporal_leakage_guardrails_by_core'] and ready['backtest_execution_by_core'] is False and ready['metric_computation_by_core'] is False and len(pkg['content_hash'])==64 and status['pending']==[]
print('PASS - Platform Core v2.53.0 Time-Series Forecasting & Backtesting runtime validation')
