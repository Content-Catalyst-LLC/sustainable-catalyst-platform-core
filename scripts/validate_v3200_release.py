#!/usr/bin/env python3
from pathlib import Path
import ast,json
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "3.2.0"' in cfg; assert 'SustainableCatalystPlatformCore/3.2.0' in cfg; assert 'analytical_result_provenance_integration_enabled: bool = True' in cfg; assert 'SC_CORE_ANALYTICAL_RESULT_PROVENANCE_INTEGRATION_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0104"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/analytical_result_provenance.py","backend/app/services/analytical_result_provenance.py","backend/tests/test_analytical_result_provenance_v3200.py","backend/scripts/validate_analytical_result_provenance.py","backend/scripts/run_v3200_release_tests.py","schemas/analytical-result-provenance-v1.schema.json","DEPLOY_PLATFORM_CORE_V3200_CONTABO.sh","PUSH_PLATFORM_CORE_V3200_FINAL.sh","PLATFORM_CORE_V3200_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("analytical_result_objects_v320","analytical_estimates_v320","analytical_uncertainty_objects_v320","analytical_lineage_bindings_v320","analytical_result_ingestion_receipts_v320","analytical_result_snapshots_v320"): assert table in models,table
svc=(R/"backend/app/services/analytical_result_provenance.py").read_text()
for invariant in ("execute_analysis_by_core","execute_r_by_core","select_provider_autonomously_by_core","infer_statistical_significance_by_core","certify_scientific_validity_by_core","determine_truth_by_core","rank_results_by_core"): assert invariant in svc,invariant
assert 'provider_version="2.1.0"' in mtext and 'workspace_adapter_release":"3.5.0"' in mtext
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 3.2.0" in wp; assert "SCPC_VERSION', '3.2.0'" in wp; assert "sc_platform_core_analytical_result_status" in wp
assert 'version = "3.2.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "3.2.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "analyticalResultBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "analytical_result_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
json.load(open(R/"schemas/analytical-result-provenance-v1.schema.json"))
print(f"PASS - dependency-free release contract; migration 0104 chars={len(migrations[-1][1])}")
print("PASS - v3.2.0 Analytical Result & Provenance Integration release contract")
