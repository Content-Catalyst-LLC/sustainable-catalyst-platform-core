from app.database import Database
from app.config import Settings
from app.migrations import migration_status
from app.services import research_methodology as svc

s=Settings.from_env(); db=Database(s.database_url); m=migration_status(db); assert '0078' in m['applied'] and m['pending']==[],m
with db.session_factory() as session:
 d=svc.readiness(session); assert d['release']=='2.74.0' and d['contract']=='sc.research.methodology-analysis.v1'
 for k in ('methodology_registry_by_core','methodology_version_registry_by_core','variable_registry_by_core','assumption_exclusion_registry_by_core','parameter_registry_by_core','execution_environment_registry_by_core','analysis_run_registry_by_core','run_input_output_registry_by_core','immutable_methodology_snapshots_by_core'): assert d[k] is True,k
 for k in ('execute_analysis_by_core','validate_results_by_core','infer_causality_by_core','judge_research_quality_by_core','infer_method_validity_by_core','select_method_by_core','alter_external_results_by_core'): assert d[k] is False,k
print('PASS - Platform Core v2.74.0 Methodology & Analysis Run Registry invariants')
