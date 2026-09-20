#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.85.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.85.0' in cfg; assert 'research_portfolio_institutional_governance_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_PORTFOLIO_INSTITUTIONAL_GOVERNANCE_ENABLED' in cfg
mod=ast.parse((R/"backend/app/migrations.py").read_text()); migrations=[]
for node in mod.body:
 if isinstance(node,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in node.targets): migrations=ast.literal_eval(node.value)
assert migrations[-1][0]=="0089"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_portfolios.py","backend/app/services/research_portfolios.py","backend/tests/test_research_portfolio_institutional_governance_v2850.py","backend/tests/test_partial_0089_recovery_v2850.py","backend/scripts/validate_research_portfolio_governance.py","schemas/research-portfolio-institutional-governance-v1.schema.json","DEPLOY_PLATFORM_CORE_V2850_CONTABO.sh","PUSH_PLATFORM_CORE_V2850_FINAL.sh","PLATFORM_CORE_V2850_TERMINAL_COMMANDS.txt")
for item in required: assert (R/item).exists(),item
models=(R/"backend/app/models.py").read_text()
for table in ("research_portfolios_v285","research_portfolio_programs_v285","research_portfolio_themes_v285","research_portfolio_objectives_v285","research_portfolio_dependencies_v285","research_portfolio_resource_envelopes_v285","research_portfolio_risks_v285","research_portfolio_reviews_v285","research_portfolio_decisions_v285","research_portfolio_revisions_v285","research_portfolio_snapshots_v285"): assert table in models,table
main=(R/"backend/app/main.py").read_text(); assert "research_portfolios" in main
service=(R/"backend/app/services/research_portfolios.py").read_text()
for invariant in ('"prioritize_programs_by_core":False','"allocate_resources_by_core":False','"allocate_funding_by_core":False','"rank_programs_by_core":False','"score_programs_by_core":False','"optimize_portfolio_by_core":False','"decide_governance_by_core":False','"infer_strategic_value_by_core":False','"forecast_program_success_by_core":False','"close_risks_by_core":False','"infer_truth_by_core":False','"summary_is_descriptive_only":True'): assert invariant in service,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.85.0" in wp; assert "SCPC_VERSION', '2.85.0'" in wp; assert "sc_platform_core_research_portfolio_status" in wp; assert "Stable tag: 2.85.0" in readme
assert 'version = "2.85.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.85.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchPortfolioBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_portfolio_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0089 chars={len(migrations[-1][1])}")
print("PASS - v2.85.0 Research Portfolio & Institutional Knowledge Governance release contract")
