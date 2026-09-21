#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.92.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.92.0' in cfg; assert 'research_project_state_versioning_reproducibility_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_PROJECT_STATE_VERSIONING_REPRODUCIBILITY_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0096"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_project_state.py","backend/app/services/research_project_state.py","backend/tests/test_research_project_state_v2920.py","backend/tests/test_partial_0096_recovery_v2920.py","backend/scripts/validate_research_project_state.py","schemas/research-project-state-versioning-v1.schema.json","DEPLOY_PLATFORM_CORE_V2920_CONTABO.sh","PUSH_PLATFORM_CORE_V2920_FINAL.sh","PLATFORM_CORE_V2920_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_project_states_v292","research_project_state_versions_v292","research_project_state_bindings_v292","research_project_state_dependencies_v292","research_project_state_environments_v292","research_project_state_checkpoints_v292","research_project_reconstruction_plans_v292","research_project_reconstruction_verifications_v292","research_project_state_revisions_v292","research_project_state_snapshots_v292"): assert table in models,table
svc=(R/"backend/app/services/research_project_state.py").read_text()
for invariant in ('restore_project_state_by_core','replay_executions_by_core','fetch_external_objects_by_core','mutate_historical_state_by_core','infer_missing_versions_by_core','infer_reproducibility_by_core','certify_reproducibility_by_core','validate_scientific_results_by_core','choose_canonical_state_by_core','determine_truth_by_core','historical_state_reconstruction_manifest_by_core','integrity_hash_chaining_by_core','summary_is_descriptive_not_reproducibility_certification'): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.92.0" in wp; assert "SCPC_VERSION', '2.92.0'" in wp; assert "sc_platform_core_research_project_state_status" in wp; assert "Stable tag: 2.92.0" in readme
assert 'version = "2.92.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.92.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchProjectStateBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_project_state_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0096 chars={len(migrations[-1][1])}")
print("PASS - v2.92.0 Research Project State, Versioning & Reproducibility release contract")
