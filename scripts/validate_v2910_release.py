#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.91.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.91.0' in cfg; assert 'cross_product_research_context_handoff_enabled: bool = True' in cfg; assert 'SC_CORE_CROSS_PRODUCT_RESEARCH_CONTEXT_HANDOFF_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0095"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_context_handoffs.py","backend/app/services/research_context_handoffs.py","backend/tests/test_research_context_handoffs_v2910.py","backend/tests/test_partial_0095_recovery_v2910.py","backend/scripts/validate_research_context_handoffs.py","schemas/research-context-handoff-v1.schema.json","DEPLOY_PLATFORM_CORE_V2910_CONTABO.sh","PUSH_PLATFORM_CORE_V2910_FINAL.sh","PLATFORM_CORE_V2910_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_context_envelopes_v291","research_context_object_bindings_v291","research_context_provenance_bindings_v291","research_context_state_markers_v291","research_handoff_protocols_v291","research_handoff_packages_v291","research_handoff_acknowledgements_v291","research_handoff_conflicts_v291","research_handoff_revisions_v291","research_handoff_snapshots_v291"): assert table in models,table
svc=(R/"backend/app/services/research_context_handoffs.py").read_text()
for invariant in ('auto_route_handoff_by_core','execute_handoff_by_core','dispatch_external_jobs_by_core','choose_target_product_by_core','mutate_source_objects_by_core','infer_missing_context_by_core','resolve_context_conflicts_by_core','authorize_access_by_core','infer_research_validity_by_core','determine_truth_by_core','declared_contract_completeness_by_core','package_integrity_verification_by_core','summary_is_descriptive_not_research_judgment'): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.91.0" in wp; assert "SCPC_VERSION', '2.91.0'" in wp; assert "sc_platform_core_research_context_handoff_status" in wp; assert "Stable tag: 2.91.0" in readme
assert 'version = "2.91.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.91.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchContextHandoffBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_context_handoff_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0095 chars={len(migrations[-1][1])}")
print("PASS - v2.91.0 Cross-Product Research Context & Handoff Protocol release contract")
