#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services.predictive_intelligence import boundaries, readiness
import os
url=os.getenv('SC_CORE_DATABASE_URL','sqlite:///./platform_core_v2550_validation.db')
db=Database(url); run_migrations(db); status=migration_status(db)
assert '0059' in status['applied'] and status['pending']==[],status
with db.session_factory() as session: r=readiness(session)
assert r['migration_0059_applied'] is True
b=boundaries()
for k in ('ensemble_registry_by_core','ensemble_member_registry_by_core','ensemble_forecast_provenance_by_core','model_comparison_study_registry_by_core','comparative_metric_evidence_by_core','pairwise_comparison_evidence_by_core','reproducible_model_comparison_packages_by_core'): assert b[k] is True,k
for k in ('ensemble_construction_by_core','ensemble_weight_optimization_by_core','ensemble_forecast_execution_by_core','model_comparison_metric_computation_by_core','statistical_significance_computation_by_core','model_ranking_by_core','automatic_model_selection'): assert b[k] is False,k
print('PASS - Platform Core v2.55.0 predictive ensembles and model comparison invariants')
