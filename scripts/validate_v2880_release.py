#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.88.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.88.0' in cfg; assert 'unified_findings_claims_inference_enabled: bool = True' in cfg; assert 'SC_CORE_UNIFIED_FINDINGS_CLAIMS_INFERENCE_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0092"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/unified_inference.py","backend/app/services/unified_inference.py","backend/tests/test_unified_findings_claims_inference_v2880.py","backend/tests/test_partial_0092_recovery_v2880.py","backend/scripts/validate_unified_inference.py","schemas/unified-findings-claims-inference-v1.schema.json","DEPLOY_PLATFORM_CORE_V2880_CONTABO.sh","PUSH_PLATFORM_CORE_V2880_FINAL.sh","PLATFORM_CORE_V2880_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_inferences_v288","research_inference_classifications_v288","research_inference_basis_bindings_v288","research_inference_assumptions_v288","research_inference_uncertainty_v288","research_inference_relations_v288","research_inference_challenges_v288","research_inference_revisions_v288","research_inference_snapshots_v288"): assert table in models,table
svc=(R/"backend/app/services/unified_inference.py").read_text()
for invariant in ('classify_automatically_by_core','generate_inferences_by_core','infer_findings_by_core','infer_claims_by_core','infer_causality_by_core','score_confidence_by_core','rank_evidence_by_core','resolve_contradictions_by_core','validate_inference_by_core','determine_truth_by_core','"summary_is_descriptive_only":True'): assert invariant in svc,invariant
for t in ('observation','measurement','descriptive_finding','statistical_inference','causal_inference','prediction','forecast','interpretation','speculation','conclusion'): assert t in svc,t
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.88.0" in wp; assert "SCPC_VERSION', '2.88.0'" in wp; assert "sc_platform_core_unified_inference_status" in wp; assert "Stable tag: 2.88.0" in readme
assert 'version = "2.88.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.88.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "inferenceBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "inference_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0092 chars={len(migrations[-1][1])}")
print("PASS - v2.88.0 Unified Findings, Claims & Inference Engine release contract")
