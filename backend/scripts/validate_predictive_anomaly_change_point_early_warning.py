#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services.predictive_intelligence import boundaries, readiness
import os
url=os.getenv('SC_CORE_DATABASE_URL','sqlite:///./platform_core_v2560_validation.db')
db=Database(url); run_migrations(db); status=migration_status(db)
assert '0060' in status['applied'] and status['pending']==[],status
with db.session_factory() as session: r=readiness(session)
assert r['migration_0060_applied'] is True
b=boundaries()
for k in ('monitoring_study_registry_by_core','detection_rule_registry_by_core','anomaly_evidence_registry_by_core','change_point_evidence_registry_by_core','early_warning_signal_registry_by_core','monitoring_episode_registry_by_core','reproducible_monitoring_packages_by_core'): assert b[k] is True,k
for k in ('anomaly_detection_by_core','change_point_detection_by_core','early_warning_computation_by_core','threshold_optimization_by_core','alert_dispatch_by_core','causal_attribution_by_core','automatic_intervention_by_core'): assert b[k] is False,k
print('PASS - Platform Core v2.56.0 anomaly, change-point, and early-warning invariants')
