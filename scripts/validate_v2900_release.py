#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.90.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.90.0' in cfg; assert 'research_workflow_orchestration_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_WORKFLOW_ORCHESTRATION_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0094"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_workflows.py","backend/app/services/research_workflows.py","backend/tests/test_research_workflow_orchestration_v2900.py","backend/tests/test_partial_0094_recovery_v2900.py","backend/scripts/validate_research_workflow_orchestration.py","schemas/research-workflow-orchestration-v1.schema.json","DEPLOY_PLATFORM_CORE_V2900_CONTABO.sh","PUSH_PLATFORM_CORE_V2900_FINAL.sh","PLATFORM_CORE_V2900_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_workflows_v290","research_workflow_stages_v290","research_workflow_transitions_v290","research_workflow_context_bindings_v290","research_workflow_handoffs_v290","research_workflow_checkpoints_v290","research_workflow_events_v290","research_workflow_policies_v290","research_workflow_revisions_v290","research_workflow_snapshots_v290"): assert table in models,table
svc=(R/"backend/app/services/research_workflows.py").read_text()
for invariant in ('choose_research_path_by_core','autonomously_advance_workflow_by_core','execute_specialist_work_by_core','dispatch_external_handoff_by_core','infer_stage_completion_by_core','approve_scientific_validity_by_core','determine_truth_by_core','apply_declared_transition_by_core','summary_is_descriptive_not_research_judgment'): assert invariant in svc,invariant
for t in ('question','search','evidence','protocol','analysis','finding','challenge','revision','publication'): assert t in svc,t
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.90.0" in wp; assert "SCPC_VERSION', '2.90.0'" in wp; assert "sc_platform_core_research_workflow_status" in wp; assert "Stable tag: 2.90.0" in readme
assert 'version = "2.90.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.90.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchWorkflowBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_workflow_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0094 chars={len(migrations[-1][1])}")
print("PASS - v2.90.0 Research Workflow & Orchestration Engine release contract")
