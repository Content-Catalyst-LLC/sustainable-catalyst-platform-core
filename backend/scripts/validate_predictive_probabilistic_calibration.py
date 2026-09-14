#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services.predictive_intelligence import boundaries, readiness
import os
url=os.getenv('SC_CORE_DATABASE_URL','sqlite:///./platform_core_v2540_validation.db')
db=Database(url); applied=run_migrations(db)
status=migration_status(db)
assert '0058' in status['applied'] and status['pending']==[],status
with db.session_factory() as session:
    r=readiness(session)
assert r['migration_0058_applied'] is True
b=boundaries()
for k in ('probabilistic_forecast_registry_by_core','calibration_study_registry_by_core','external_calibration_mapping_registry_by_core','proper_scoring_evidence_registry_by_core','reproducible_calibration_packages_by_core'): assert b[k] is True,k
for k in ('probabilistic_inference_execution_by_core','calibration_mapping_fitting_by_core','calibration_mapping_application_by_core','proper_scoring_rule_computation_by_core','probabilistic_model_ranking_by_core'): assert b[k] is False,k
print('PASS - Platform Core v2.54.0 probabilistic forecasting and calibration invariants')
