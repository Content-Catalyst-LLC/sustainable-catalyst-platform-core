from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.visual_linked_views import boundaries
s=Settings();db=Database(s.database_url);run_migrations(db);m=migration_status(db);assert '0068' in m['applied'] and m['pending']==[],m
b=boundaries();assert b['cross_filter_predicate_registry_by_core'] and b['immutable_linked_view_snapshots_by_core'];assert b['query_execution_by_core'] is False and b['data_filtering_by_core'] is False
print('PASS - Platform Core v2.64.0 Linked Views & Cross-Filtering invariants')
