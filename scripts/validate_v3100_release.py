#!/usr/bin/env python3
from pathlib import Path
import ast,json
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "3.1.0"' in cfg; assert 'SustainableCatalystPlatformCore/3.1.0' in cfg; assert 'analytical_runtime_provider_contract_enabled: bool = True' in cfg; assert 'SC_CORE_ANALYTICAL_RUNTIME_PROVIDER_CONTRACT_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0103"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/analytical_runtime_provider.py","backend/app/services/analytical_runtime_provider.py","backend/tests/test_analytical_runtime_provider_v3100.py","backend/scripts/validate_analytical_runtime_provider.py","schemas/analytical-runtime-provider-v1.schema.json","DEPLOY_PLATFORM_CORE_V3100_CONTABO.sh","PUSH_PLATFORM_CORE_V3100_FINAL.sh","PLATFORM_CORE_V3100_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("analytical_runtime_providers_v310","analytical_capabilities_v310","analytical_execution_requests_v310","analytical_runtime_environments_v310","analytical_execution_results_v310","analytical_artifacts_v310","statistical_diagnostics_v310","analytical_reproduction_references_v310"): assert table in models,table
svc=(R/"backend/app/services/analytical_runtime_provider.py").read_text()
for invariant in ("execute_analysis_by_core","execute_r_by_core","execute_python_by_core","execute_julia_by_core","select_provider_autonomously_by_core","infer_statistical_significance_by_core","certify_scientific_validity_by_core","determine_truth_by_core"): assert invariant in svc,invariant
assert 'provider_key="catalystanalyticsr"' in mtext and 'provider_version="2.0.1"' in mtext and 'runtime="r"' in mtext and 'execution_host="workspace"' in mtext
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 3.1.0" in wp; assert "SCPC_VERSION', '3.1.0'" in wp; assert "sc_platform_core_analytical_runtime_status" in wp
assert 'version = "3.1.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "3.1.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "analyticalRuntimeProviders" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "analytical_runtime_providers" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
json.load(open(R/"schemas/analytical-runtime-provider-v1.schema.json"))
print(f"PASS - dependency-free release contract; migration 0103 chars={len(migrations[-1][1])}")
print("PASS - v3.1.0 Analytical Runtime Provider Contract release contract")
