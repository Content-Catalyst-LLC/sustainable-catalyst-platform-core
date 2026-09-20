#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.83.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.83.0' in cfg; assert 'cross_study_evidence_synthesis_enabled: bool = True' in cfg; assert 'SC_CORE_CROSS_STUDY_EVIDENCE_SYNTHESIS_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
    if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0087"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/cross_study_synthesis.py","backend/app/services/cross_study_synthesis.py","backend/tests/test_cross_study_evidence_synthesis_v2830.py","backend/tests/test_partial_0087_recovery_v2830.py","schemas/research-cross-study-evidence-synthesis-v1.schema.json","DEPLOY_PLATFORM_CORE_V2830_CONTABO.sh","PUSH_PLATFORM_CORE_V2830_FINAL.sh","PLATFORM_CORE_V2830_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_evidence_syntheses_v283","research_synthesis_studies_v283","research_synthesis_outcomes_v283","research_synthesis_effects_v283","research_meta_analyses_v283","research_meta_research_assessments_v283","research_synthesis_relations_v283","research_evidence_gaps_v283","research_evidence_synthesis_revisions_v283","research_evidence_synthesis_snapshots_v283"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "cross_study_synthesis" in main
service=(R/"backend/app/services/cross_study_synthesis.py").read_text()
for invariant in ('"search_literature_by_core": False','"decide_study_inclusion_by_core": False','"compute_effect_size_by_core": False','"pool_estimates_by_core": False','"score_study_quality_by_core": False','"infer_bias_by_core": False','"infer_causality_by_core": False','"infer_truth_by_core": False','"summary_is_descriptive_only":True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.83.0" in wp; assert "SCPC_VERSION', '2.83.0'" in wp; assert "sc_platform_core_evidence_synthesis_status" in wp; assert "Stable tag: 2.83.0" in readme
assert 'version = "2.83.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.83.0"' in (R/"backend/public_sdk/javascript/package.json").read_text()
print(f"PASS - dependency-free release contract; migration 0087 chars={len(migrations[-1][1])}")
print("PASS - v2.83.0 Cross-Study Evidence Synthesis & Meta-Research release contract")
