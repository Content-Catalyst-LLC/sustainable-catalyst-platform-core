#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.86.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.86.0' in cfg; assert 'scientific_study_investigation_protocol_enabled: bool = True' in cfg; assert 'SC_CORE_SCIENTIFIC_STUDY_INVESTIGATION_PROTOCOL_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
 if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0090"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_protocols.py","backend/app/services/research_protocols.py","backend/tests/test_scientific_study_investigation_protocol_v2860.py","backend/tests/test_partial_0090_recovery_v2860.py","backend/scripts/validate_research_protocols.py","schemas/scientific-study-investigation-protocol-v1.schema.json","DEPLOY_PLATFORM_CORE_V2860_CONTABO.sh","PUSH_PLATFORM_CORE_V2860_FINAL.sh","PLATFORM_CORE_V2860_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("scientific_research_protocols_v286","scientific_protocol_objectives_v286","scientific_protocol_scope_units_v286","scientific_protocol_measures_v286","scientific_protocol_source_plans_v286","scientific_protocol_acquisition_plans_v286","scientific_protocol_method_plans_v286","scientific_protocol_assumptions_v286","scientific_protocol_validation_plans_v286","scientific_protocol_output_plans_v286","scientific_protocol_deviations_v286","scientific_protocol_revisions_v286","scientific_protocol_snapshots_v286"): assert table in models,table
service=(R/"backend/app/services/research_protocols.py").read_text()
for invariant in ('execute_protocol_by_core','collect_data_by_core','run_analysis_by_core','infer_causality_by_core','certify_ethics_by_core','infer_truth_by_core','"summary_is_descriptive_only":True'): assert invariant in service,invariant
assert "**{k:False for k in FORBIDDEN}" in service
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.86.0" in wp; assert "SCPC_VERSION', '2.86.0'" in wp; assert "sc_platform_core_research_protocol_status" in wp; assert "Stable tag: 2.86.0" in readme
assert 'version = "2.86.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.86.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchProtocolBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_protocol_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0090 chars={len(migrations[-1][1])}")
print("PASS - v2.86.0 Scientific Study & Investigation Protocol Model release contract")
