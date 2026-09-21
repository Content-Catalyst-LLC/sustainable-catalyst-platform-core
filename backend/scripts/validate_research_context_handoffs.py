#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import research_context_handoffs as svc
from sqlalchemy import inspect
db=Database("sqlite:///:memory:"); run_migrations(db); st=migration_status(db); assert "0095" in st["applied"] and st["pending"]==[]
names=set(inspect(db.engine).get_table_names()); expected={"research_context_envelopes_v291","research_context_object_bindings_v291","research_context_provenance_bindings_v291","research_context_state_markers_v291","research_handoff_protocols_v291","research_handoff_packages_v291","research_handoff_acknowledgements_v291","research_handoff_conflicts_v291","research_handoff_revisions_v291","research_handoff_snapshots_v291"}; assert expected<=names
with db.session_factory() as s:
 d=svc.readiness(s); assert d["release"]=="2.91.0" and d["context_envelope_registry_by_core"] is True and d["auto_route_handoff_by_core"] is False and d["determine_truth_by_core"] is False
print("PASS - Platform Core v2.91.0 Cross-Product Research Context & Handoff Protocol invariants")
