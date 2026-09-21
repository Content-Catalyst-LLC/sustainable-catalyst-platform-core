#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.97.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.97.0' in cfg; assert 'platform_research_integration_certification_enabled: bool = True' in cfg; assert 'SC_CORE_PLATFORM_RESEARCH_INTEGRATION_CERTIFICATION_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0101"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/platform_research_certification.py","backend/app/services/platform_research_certification.py","backend/tests/test_platform_research_integration_certification_v2970.py","backend/tests/test_partial_0101_recovery_v2970.py","backend/scripts/validate_platform_research_integration_certification.py","schemas/platform-research-integration-certification-v1.schema.json","DEPLOY_PLATFORM_CORE_V2970_CONTABO.sh","PUSH_PLATFORM_CORE_V2970_FINAL.sh","PLATFORM_CORE_V2970_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_integration_certification_suites_v297","research_integration_certification_products_v297","research_integration_certification_cases_v297","research_integration_certification_runs_v297","research_integration_certification_case_results_v297","research_integration_certification_exchange_checks_v297","research_integration_certification_trace_checks_v297","research_integration_certification_reproduction_checks_v297","research_integration_certification_evidence_v297","research_integration_certification_findings_v297","research_integration_certification_revisions_v297","research_integration_certification_snapshots_v297"): assert table in models,table
svc=(R/"backend/app/services/platform_research_certification.py").read_text()
for invariant in ("invoke_product_by_core","execute_conformance_case_by_core","certify_scientific_validity_by_core","certify_product_quality_by_core","authorize_product_by_certification_by_core","rank_products_by_core","infer_missing_evidence_by_core","infer_reproducibility_by_core","resolve_failed_case_by_core","determine_truth_by_core","certification_means_runtime_contract_conformance_not_scientific_validity"): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 2.97.0" in wp; assert "SCPC_VERSION', '2.97.0'" in wp; assert "sc_platform_core_research_integration_certification_status" in wp
assert 'version = "2.97.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.97.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchIntegrationCertificationSuite" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_integration_certification_suite" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0101 chars={len(migrations[-1][1])}")
print("PASS - v2.97.0 Platform Research Integration Certification release contract")
