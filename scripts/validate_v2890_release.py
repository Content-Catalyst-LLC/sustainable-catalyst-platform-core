#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.89.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.89.0' in cfg; assert 'research_quality_bias_methodological_audit_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_QUALITY_BIAS_METHODOLOGICAL_AUDIT_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0093"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_quality_audit.py","backend/app/services/research_quality_audit.py","backend/tests/test_research_quality_bias_methodological_audit_v2890.py","backend/tests/test_partial_0093_recovery_v2890.py","backend/scripts/validate_research_quality_audit.py","schemas/research-quality-bias-methodological-audit-v1.schema.json","DEPLOY_PLATFORM_CORE_V2890_CONTABO.sh","PUSH_PLATFORM_CORE_V2890_FINAL.sh","PLATFORM_CORE_V2890_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_quality_audits_v289","research_quality_audit_subjects_v289","research_quality_audit_checks_v289","research_quality_audit_findings_v289","research_quality_audit_evidence_v289","research_quality_bias_assessments_v289","research_quality_method_assessments_v289","research_quality_audit_responses_v289","research_quality_audit_revisions_v289","research_quality_audit_snapshots_v289"): assert table in models,table
svc=(R/"backend/app/services/research_quality_audit.py").read_text()
for invariant in ('infer_bias_by_core','score_research_quality_by_core','rank_studies_by_core','determine_method_validity_by_core','infer_confounding_by_core','determine_causal_validity_by_core','resolve_contradictions_by_core','verify_citation_support_by_core','certify_reproducibility_by_core','certify_ethics_by_core','reject_research_by_core','determine_truth_by_core','coverage_is_descriptive_not_a_quality_score'): assert invariant in svc,invariant
for t in ('confounding','selection_bias','measurement_bias','missing_data','unsupported_causal_claim','statistical_method','uncertainty','citation_support','contradictory_finding','protocol_deviation','reproducibility'): assert t in svc,t
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.89.0" in wp; assert "SCPC_VERSION', '2.89.0'" in wp; assert "sc_platform_core_research_quality_audit_status" in wp; assert "Stable tag: 2.89.0" in readme
assert 'version = "2.89.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.89.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "qualityAuditBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "quality_audit_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0093 chars={len(migrations[-1][1])}")
print("PASS - v2.89.0 Research Quality, Bias & Methodological Audit Engine release contract")
