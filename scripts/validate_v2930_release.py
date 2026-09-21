#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.93.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.93.0' in cfg; assert 'research_roles_agents_contributor_provenance_enabled: bool = True' in cfg; assert 'SC_CORE_RESEARCH_ROLES_AGENTS_CONTRIBUTOR_PROVENANCE_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0097"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/research_contributor_provenance.py","backend/app/services/research_contributor_provenance.py","backend/tests/test_research_contributor_provenance_v2930.py","backend/tests/test_partial_0097_recovery_v2930.py","backend/scripts/validate_research_contributor_provenance.py","schemas/research-roles-agents-contributor-provenance-v1.schema.json","DEPLOY_PLATFORM_CORE_V2930_CONTABO.sh","PUSH_PLATFORM_CORE_V2930_FINAL.sh","PLATFORM_CORE_V2930_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("research_contributors_v293","research_role_definitions_v293","research_role_assignments_v293","research_contributions_v293","research_agent_profiles_v293","research_agent_actions_v293","research_authorship_assertions_v293","research_responsibility_statements_v293","research_contribution_reviews_v293","research_contributor_revisions_v293","research_contributor_snapshots_v293"): assert table in models,table
svc=(R/"backend/app/services/research_contributor_provenance.py").read_text()
for invariant in ('assign_roles_by_core','authorize_agents_by_core','execute_agent_actions_by_core','infer_contributor_identity_by_core','infer_authorship_by_core','rank_contributors_by_core','score_contributions_by_core','infer_responsibility_by_core','grant_permissions_by_core','decide_credit_by_core','determine_truth_by_core','human_ai_tool_distinction_by_core','attribution_is_declared_not_core_decided'): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); readme=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text(); assert "Version: 2.93.0" in wp; assert "SCPC_VERSION', '2.93.0'" in wp; assert "sc_platform_core_research_contributor_provenance_status" in wp; assert "Stable tag: 2.93.0" in readme
assert 'version = "2.93.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.93.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "researchContributorProvenanceBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "research_contributor_provenance_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0097 chars={len(migrations[-1][1])}")
print("PASS - v2.93.0 Research Roles, Agents & Contributor Provenance Framework release contract")
