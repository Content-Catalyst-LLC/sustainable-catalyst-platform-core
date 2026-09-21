from app.database import Database,Base
from app.migrations import run_migrations,migration_status
from app.models import ResearchContextEnvelopeRecord,ResearchContextObjectBindingRecord

def test_partial_0095_recovery(tmp_path):
 db=Database("sqlite:///"+str(tmp_path/"partial.db")); ResearchContextEnvelopeRecord.__table__.create(db.engine,checkfirst=True); ResearchContextObjectBindingRecord.__table__.create(db.engine,checkfirst=True); run_migrations(db); st=migration_status(db); assert "0095" in st["applied"] and st["pending"]==[]; names=set(__import__("sqlalchemy").inspect(db.engine).get_table_names()); expected={"research_context_envelopes_v291","research_context_object_bindings_v291","research_context_provenance_bindings_v291","research_context_state_markers_v291","research_handoff_protocols_v291","research_handoff_packages_v291","research_handoff_acknowledgements_v291","research_handoff_conflicts_v291","research_handoff_revisions_v291","research_handoff_snapshots_v291"}; assert expected<=names
