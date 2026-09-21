#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.87.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.87.0' in cfg; assert 'computation_analysis_execution_lineage_enabled: bool = True' in cfg; assert 'SC_CORE_COMPUTATION_ANALYSIS_EXECUTION_LINEAGE_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0091"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/computation_lineage.py","backend/app/services/computation_lineage.py","backend/tests/test_computation_analysis_execution_lineage_v2870.py","backend/tests/test_partial_0091_recovery_v2870.py","backend/scripts/validate_computation_lineage.py","schemas/computation-analysis-execution-lineage-v1.schema.json","DEPLOY_PLATFORM_CORE_V2870_CONTABO.sh","PUSH_PLATFORM_CORE_V2870_FINAL.sh","PLATFORM_CORE_V2870_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("computation_executions_v287","computation_execution_inputs_v287","computation_execution_parameters_v287","computation_execution_assumptions_v287","computation_execution_environments_v287","computation_execution_steps_v287","computation_execution_outputs_v287","computation_research_bindings_v287","computation_execution_dependencies_v287","computation_execution_verifications_v287","computation_execution_revisions_v287","computation_execution_snapshots_v287"): assert table in models,table
svc=(R/"backend/app/services/computation_lineage.py").read_text()
for invariant in ('execute_code_by_core','run_python_by_core','run_r_by_core','run_julia_by_core','run_workbench_by_core','train_ml_by_core','infer_findings_by_core','infer_claims_by_core','infer_reproducibility_by_core','"summary_is_descriptive_only":True'): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.87.0" in wp; assert "SCPC_VERSION', '2.87.0'" in wp; assert "sc_platform_core_computation_lineage_status" in wp; assert "Stable tag: 2.87.0" in readme
assert 'version = "2.87.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.87.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "computationLineageBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "computation_lineage_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0091 chars={len(migrations[-1][1])}")
print("PASS - v2.87.0 Computation, Analysis & Execution Lineage release contract")
