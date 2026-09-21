#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_contributor_provenance as svc
from sqlalchemy import inspect
db=Database("sqlite:///:memory:"); run_migrations(db); st=migration_status(db); assert "0097" in st["applied"] and st["pending"]==[]
names=set(inspect(db.engine).get_table_names()); expected={"research_contributors_v293","research_role_definitions_v293","research_role_assignments_v293","research_contributions_v293","research_agent_profiles_v293","research_agent_actions_v293","research_authorship_assertions_v293","research_responsibility_statements_v293","research_contribution_reviews_v293","research_contributor_revisions_v293","research_contributor_snapshots_v293"}; assert expected<=names
with db.session_factory() as s:
 d=svc.readiness(s); assert d["release"]=="2.93.0" and d["human_ai_tool_distinction_by_core"] is True and d["execute_agent_actions_by_core"] is False and d["decide_credit_by_core"] is False and d["determine_truth_by_core"] is False
print("PASS - Platform Core v2.93.0 Research Roles, Agents & Contributor Provenance Framework invariants")
