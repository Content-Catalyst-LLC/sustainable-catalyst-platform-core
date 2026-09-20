#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.81.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.81.0' in cfg; assert 'reproducible_research_publication_enabled: bool = True' in cfg; assert 'SC_CORE_REPRODUCIBLE_RESEARCH_PUBLICATION_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
    if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0085"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_publications.py","backend/app/services/research_publications.py","backend/tests/test_reproducible_research_publication_v2810.py","backend/tests/test_partial_0085_recovery_v2810.py","schemas/research-reproducible-publication-v1.schema.json","DEPLOY_PLATFORM_CORE_V2810_CONTABO.sh","PUSH_PLATFORM_CORE_V2810_FINAL.sh","PLATFORM_CORE_V2810_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_publications_v281","research_publication_sections_v281","research_publication_references_v281","research_publication_citations_v281","research_publication_figures_v281","research_publication_supplements_v281","research_publication_identifiers_v281","research_publication_exports_v281","research_publication_revisions_v281","research_publication_snapshots_v281"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "research_publications" in main
service=(R/"backend/app/services/research_publications.py").read_text()
for invariant in ('"generate_manuscript_by_core":False','"fabricate_citation_by_core":False','"judge_publication_quality_by_core":False','"issue_doi_by_core":False','"publish_external_by_core":False','"diagnostic_is_structural_only":True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.81.0" in wp; assert "SCPC_VERSION', '2.81.0'" in wp; assert "sc_platform_core_research_publication_status" in wp; assert "Stable tag: 2.81.0" in readme
assert 'version = "2.81.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.81.0"' in (R/"backend/public_sdk/javascript/package.json").read_text()
print(f"PASS - dependency-free release contract; migration 0085 chars={len(migrations[-1][1])}")
print("PASS - v2.81.0 Reproducible Research Publication & Scholarly Output release contract")
