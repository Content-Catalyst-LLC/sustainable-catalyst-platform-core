#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services import peer_review_intelligence as svc
db=Database("sqlite:///:memory:"); run_migrations(db)
with db.session_factory() as s:
    r=svc.readiness(s); assert r["release"]=="2.82.0"; assert r["generate_peer_review_by_core"] is False; assert r["score_manuscript_quality_by_core"] is False; assert r["infer_replication_success_by_core"] is False; assert r["decide_publication_by_core"] is False
assert "0086" in migration_status(db)["applied"]
print("PASS - Platform Core v2.82.0 Peer Review, Replication & Rebuttal invariants")
