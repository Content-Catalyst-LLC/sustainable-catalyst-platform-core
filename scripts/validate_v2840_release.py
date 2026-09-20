#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.84.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.84.0' in cfg; assert 'research_program_longitudinal_knowledge_graph_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_PROGRAM_LONGITUDINAL_KNOWLEDGE_GRAPH_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
    if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0088"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_programs.py","backend/app/services/research_programs.py","backend/tests/test_research_program_longitudinal_graph_v2840.py","backend/tests/test_partial_0088_recovery_v2840.py","backend/scripts/validate_research_program_longitudinal_graph.py","schemas/research-program-longitudinal-knowledge-graph-v1.schema.json","DEPLOY_PLATFORM_CORE_V2840_CONTABO.sh","PUSH_PLATFORM_CORE_V2840_FINAL.sh","PLATFORM_CORE_V2840_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_programs_v284","research_program_projects_v284","research_program_objectives_v284","research_program_milestones_v284","research_longitudinal_nodes_v284","research_longitudinal_edges_v284","research_knowledge_states_v284","research_evolution_events_v284","research_program_revisions_v284","research_program_snapshots_v284"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "research_programs" in main
service=(R/"backend/app/services/research_programs.py").read_text()
for invariant in ('"prioritize_research_by_core": False','"allocate_funding_by_core": False','"rank_projects_by_core": False','"auto_link_knowledge_graph_by_core": False','"infer_research_direction_by_core": False','"infer_causality_by_core": False','"forecast_program_success_by_core": False','"resolve_evidence_gaps_by_core": False','"infer_knowledge_truth_by_core": False','"infer_truth_by_core": False','"summary_is_descriptive_only":True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.84.0" in wp; assert "SCPC_VERSION', '2.84.0'" in wp; assert "sc_platform_core_research_program_status" in wp; assert "Stable tag: 2.84.0" in readme
assert 'version = "2.84.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.84.0"' in (R/"backend/public_sdk/javascript/package.json").read_text()
assert "researchProgramBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_program_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0088 chars={len(migrations[-1][1])}")
print("PASS - v2.84.0 Research Program & Longitudinal Knowledge Graph release contract")
