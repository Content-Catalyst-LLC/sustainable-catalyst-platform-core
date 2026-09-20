#!/usr/bin/env python3
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from sqlalchemy import inspect
app=create_app(Settings(database_url='sqlite:////tmp/sc-core-v2770-validator.db'))
db=app.state.database
tables={'research_findings','research_finding_revisions','research_interpretations','research_claims_v277','research_claim_revisions_v277','research_evidence_links_v277','research_derivation_links_v277','research_contradictions_v277','research_intelligence_snapshots_v277'}
assert tables.issubset(set(inspect(db.engine).get_table_names()))
s=migration_status(db);assert '0081' in s['applied'] and s['pending']==[],s
print('PASS - Platform Core v2.77.0 Finding, Claim & Evidence Intelligence invariants')
