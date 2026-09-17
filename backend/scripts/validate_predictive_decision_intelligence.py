#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.predictive_intelligence import boundaries
from sqlalchemy import inspect
s=Settings(); db=Database(s.database_url); run_migrations(db); status=migration_status(db)
tables=set(inspect(db.engine).get_table_names())
required={'predictive_decision_studies','predictive_decision_options','predictive_decision_criteria','predictive_decision_evidence_bindings','predictive_decision_scenario_assessments','predictive_decision_evaluations','predictive_decision_handoffs','predictive_decision_packages'}
assert required <= tables,(required-tables)
assert status['pending']==[] and status['applied'][-1]=='0063',status
b=boundaries()
for k in ('predictive_decision_study_registry_by_core','decision_option_registry_by_core','decision_criterion_registry_by_core','decision_evidence_binding_registry_by_core','decision_scenario_assessment_registry_by_core','decision_evaluation_evidence_registry_by_core','decision_handoff_registry_by_core','reproducible_predictive_decision_packages_by_core'): assert b[k] is True,k
for k in ('decision_ranking_by_core','decision_recommendation_by_core','decision_optimization_by_core','utility_computation_by_core','regret_computation_by_core','constraint_solving_by_core','decision_action_execution_by_core','automatic_action_selection'): assert b[k] is False,k
print('PASS - Platform Core v2.59.0 predictive decision intelligence invariants')
