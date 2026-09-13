from sqlalchemy import inspect
from app.database import Base,Database
from app.migrations import MIGRATIONS,migration_status,run_migrations
from app.models import SchemaMigration
TABLES={'spatial_temporal_scenes','spatial_temporal_features','spatial_temporal_events','spatial_temporal_trajectories','spatial_temporal_trajectory_points','spatial_temporal_changes','spatial_temporal_views'}

def test_partial_0042_table_state_recovers_by_recording_short_metadata(tmp_path):
    db=Database(f"sqlite:///{tmp_path/'partial0042.db'}")
    Base.metadata.create_all(db.engine)
    assert TABLES <= set(inspect(db.engine).get_table_names())
    with db.session_factory() as s:
        for version,description in MIGRATIONS:
            if version=='0042':break
            s.add(SchemaMigration(version=version,description=description))
        s.commit(); assert s.get(SchemaMigration,'0042') is None
    assert run_migrations(db)==['0042','0043','0044','0045']
    with db.session_factory() as s:
        row=s.get(SchemaMigration,'0042'); assert row and len(row.description)<=300
    status=migration_status(db);assert status['pending']==[] and status['applied'][-1]=='0045'
    assert TABLES <= set(inspect(db.engine).get_table_names())
