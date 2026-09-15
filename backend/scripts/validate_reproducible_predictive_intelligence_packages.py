#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.predictive_intelligence import boundaries
from sqlalchemy import inspect
s=Settings(); db=Database(s.database_url); run_migrations(db); status=migration_status(db)
tables=set(inspect(db.engine).get_table_names())
required={'predictive_intelligence_packages','predictive_intelligence_package_components','predictive_intelligence_package_artifacts','predictive_intelligence_package_environments','predictive_intelligence_package_verifications','predictive_intelligence_package_reviews','predictive_intelligence_package_snapshots'}
assert required <= tables,(required-tables)
assert status['pending']==[] and status['applied'][-1]=='0064',status
b=boundaries()
for k in ('reproducible_predictive_package_registry_by_core','predictive_package_component_manifest_by_core','predictive_package_artifact_registry_by_core','predictive_package_environment_registry_by_core','predictive_package_verification_registry_by_core','predictive_package_review_registry_by_core','immutable_predictive_package_snapshots_by_core','cross_predictive_layer_packaging_by_core'): assert b[k] is True,k
for k in ('predictive_execution_by_core','model_refitting_by_core','forecast_regeneration_by_core','backtest_reexecution_by_core','calibration_reexecution_by_core','causal_estimation_by_core','decision_optimization_by_core','automatic_reproduction_by_core','automatic_truth_promotion'): assert b[k] is False,k
print('PASS - Platform Core v2.60.0 reproducible predictive intelligence package invariants')
