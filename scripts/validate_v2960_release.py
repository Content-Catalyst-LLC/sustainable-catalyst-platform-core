#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.96.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.96.0' in cfg; assert 'unified_research_runtime_contract_enabled: bool = True' in cfg; assert 'SC_CORE_UNIFIED_RESEARCH_RUNTIME_CONTRACT_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0100"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/unified_research_runtime.py","backend/app/services/unified_research_runtime.py","backend/tests/test_unified_research_runtime_v2960.py","backend/tests/test_partial_0100_recovery_v2960.py","backend/scripts/validate_unified_research_runtime.py","schemas/research-unified-runtime-contract-v1.schema.json","DEPLOY_PLATFORM_CORE_V2960_CONTABO.sh","PUSH_PLATFORM_CORE_V2960_FINAL.sh","PLATFORM_CORE_V2960_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_runtime_contracts_v296","research_runtime_object_types_v296","research_runtime_operations_v296","research_runtime_capabilities_v296","research_runtime_product_bindings_v296","research_runtime_exchange_envelopes_v296","research_runtime_invocations_v296","research_runtime_result_bindings_v296","research_runtime_compatibility_assertions_v296","research_runtime_revisions_v296","research_runtime_snapshots_v296"): assert table in models,table
svc=(R/"backend/app/services/unified_research_runtime.py").read_text()
for invariant in ("execute_specialist_work_by_core","auto_route_requests_by_core","infer_object_schema_by_core","mutate_specialist_state_by_core","authorize_product_by_contract_by_core","validate_scientific_result_by_core","resolve_semantic_conflict_by_core","certify_reproducibility_by_core","invoke_external_runtime_by_core","determine_truth_by_core","contract_semantics_declared_not_inferred"): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 2.96.0" in wp; assert "SCPC_VERSION', '2.96.0'" in wp; assert "sc_platform_core_unified_research_runtime_status" in wp
assert 'version = "2.96.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.96.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchRuntimeContractBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_runtime_contract_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0100 chars={len(migrations[-1][1])}")
print("PASS - v2.96.0 Unified Research Runtime Contract release contract")
