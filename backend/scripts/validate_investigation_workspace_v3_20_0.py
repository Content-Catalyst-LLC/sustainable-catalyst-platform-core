#!/usr/bin/env python3
from sqlalchemy import inspect
from app.config import Settings
from app.database import Database
from app import models
from app.main import app
expected={'investigation_workspaces','investigation_workspace_objects','investigation_workspace_relations','investigation_workspace_views','investigation_workspace_snapshots','investigation_workspace_handoffs'}
db=Database(Settings().database_url); found=set(inspect(db.engine).get_table_names()); missing=expected-found
assert not missing, f'missing tables: {sorted(missing)}'
routes={getattr(x,'path',None) for x in app.routes}; assert '/api/v1/investigation-workspace/capabilities' in routes
print('Platform Core v3.20.0 runtime validation: PASS')
