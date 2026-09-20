#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.80.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.80.0' in cfg; assert 'research_decision_trace_conclusion_governance_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_DECISION_TRACE_CONCLUSION_GOVERNANCE_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
    if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0084"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_conclusions.py","backend/app/services/research_conclusions.py","backend/tests/test_research_decision_trace_conclusion_governance_v2800.py","backend/tests/test_partial_0084_recovery_v2800.py","schemas/research-decision-trace-conclusion-governance-v1.schema.json","DEPLOY_PLATFORM_CORE_V2800_CONTABO.sh","PUSH_PLATFORM_CORE_V2800_FINAL.sh","PLATFORM_CORE_V2800_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_conclusions_v280","research_conclusion_evidence_bindings_v280","research_conclusion_caveats_v280","research_conclusion_dissent_v280","research_decision_traces_v280","research_conclusion_reviews_v280","research_conclusion_revisions_v280","research_conclusion_snapshots_v280"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "research_conclusions" in main
service=(R/"backend/app/services/research_conclusions.py").read_text()
for invariant in ('"generate_conclusion_by_core": False','"choose_conclusion_by_core": False','"score_conclusion_by_core": False','"rank_conclusions_by_core": False','"certify_conclusion_by_core": False','"infer_truth_by_core": False','"governance_summary_is_descriptive_only":True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.80.0" in wp; assert "SCPC_VERSION', '2.80.0'" in wp; assert "sc_platform_core_research_conclusion_status" in wp; assert "Stable tag: 2.80.0" in readme
assert 'version = "2.80.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.80.0"' in (R/"backend/public_sdk/javascript/package.json").read_text()
print(f"PASS - dependency-free release contract; migration ledger max=300, 0084 chars={len(migrations[-1][1])}")
print("PASS - v2.80.0 Research Decision Trace & Conclusion Governance release contract")
