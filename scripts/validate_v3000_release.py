#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "3.0.0"' in cfg; assert 'SustainableCatalystPlatformCore/3.0.0' in cfg; assert 'unified_research_scientific_investigation_runtime_enabled: bool = True' in cfg; assert 'SC_CORE_UNIFIED_RESEARCH_SCIENTIFIC_INVESTIGATION_RUNTIME_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0102"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/unified_research_scientific_runtime.py","backend/app/services/unified_research_scientific_runtime.py","backend/tests/test_unified_research_scientific_investigation_runtime_v3000.py","backend/tests/test_partial_0102_recovery_v3000.py","backend/scripts/validate_unified_research_scientific_runtime.py","schemas/unified-research-scientific-investigation-runtime-v1.schema.json","DEPLOY_PLATFORM_CORE_V3000_CONTABO.sh","PUSH_PLATFORM_CORE_V3000_FINAL.sh","PLATFORM_CORE_V3000_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("unified_research_runtime_sessions_v300","unified_research_runtime_object_bindings_v300","unified_research_runtime_product_bindings_v300","unified_research_runtime_execution_bindings_v300","unified_research_runtime_investigation_bindings_v300","unified_research_runtime_visual_bindings_v300","unified_research_runtime_validation_bindings_v300","unified_research_runtime_package_bindings_v300","unified_research_runtime_handoff_bindings_v300","unified_research_runtime_milestones_v300","unified_research_runtime_revisions_v300","unified_research_runtime_snapshots_v300"): assert table in models,table
svc=(R/"backend/app/services/unified_research_scientific_runtime.py").read_text()
for invariant in ("execute_scientific_work_by_core","execute_code_by_core","run_investigation_by_core","infer_findings_by_core","infer_causality_by_core","select_hypothesis_by_core","rank_evidence_by_core","render_visuals_by_core","publish_research_by_core","authorize_access_by_core","certify_scientific_validity_by_core","determine_truth_by_core"): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 3.0.0" in wp; assert "SCPC_VERSION', '3.0.0'" in wp; assert "sc_platform_core_unified_research_runtime_status" in wp
assert 'version = "3.0.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "3.0.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "unifiedResearchRuntimeBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "unified_research_runtime_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0102 chars={len(migrations[-1][1])}")
print("PASS - v3.0.0 Unified Research, Scientific Computing & Investigation Runtime release contract")
