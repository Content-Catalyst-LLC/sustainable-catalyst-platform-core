#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_publications as svc
db=Database("sqlite:///:memory:"); run_migrations(db)
with db.session_factory() as s:
 r=svc.readiness(s); assert r["release"]=="2.81.0"; assert r["generate_manuscript_by_core"] is False; assert r["fabricate_citation_by_core"] is False; assert r["publish_external_by_core"] is False
assert "0085" in migration_status(db)["applied"]
print("PASS - Platform Core v2.81.0 Reproducible Research Publication invariants")
